"""Unit tests for LGHorizonApi."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lghorizon.lghorizon_api import LGHorizonApi
from lghorizon.lghorizon_device import LGHorizonDevice
from lghorizon.lghorizon_models import (
    LGHorizonAuth,
    LGHorizonChannel,
    LGHorizonCustomer,
    LGHorizonMessageType,
    LGHorizonRunningState,
    LGHorizonStatusMessage,
    LGHorizonUIStatusMessage,
    LGHorizonRecordingList,
    LGHorizonRecordingQuota,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_api(mock_auth, profile_id="profile-1") -> LGHorizonApi:
    """Return a fresh, *un-initialized* LGHorizonApi instance."""
    return LGHorizonApi(mock_auth, profile_id=profile_id)


def make_initialized_api(mock_auth, sample_customer_json, sample_channel_json):
    """Return an api with manually set internal state (no real connections)."""
    api = make_api(mock_auth)
    api._initialized = True
    api._customer = LGHorizonCustomer(sample_customer_json)
    api._channels = {"channel-1": LGHorizonChannel(sample_channel_json)}
    api._mqtt_client = MagicMock()
    api._mqtt_client.disconnect = AsyncMock()
    return api


# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_stores_auth(self, mock_auth):
        api = make_api(mock_auth)
        assert api.auth is mock_auth

    def test_stores_profile_id(self, mock_auth):
        api = make_api(mock_auth, profile_id="profile-42")
        assert api._profile_id == "profile-42"

    def test_devices_is_empty_dict_instance_level(self, mock_auth):
        """Each instance must have its own _devices dict (not a class-level shared dict)."""
        api1 = make_api(mock_auth)
        api2 = make_api(mock_auth)
        assert api1._devices == {}
        assert api2._devices == {}
        # Mutating one must not affect the other
        api1._devices["x"] = MagicMock()
        assert "x" not in api2._devices

    def test_initialized_is_false(self, mock_auth):
        api = make_api(mock_auth)
        assert api._initialized is False

    def test_mqtt_client_is_none(self, mock_auth):
        api = make_api(mock_auth)
        assert api._mqtt_client is None


# ---------------------------------------------------------------------------
# get_devices()
# ---------------------------------------------------------------------------


class TestGetDevices:
    async def test_raises_if_not_initialized(self, mock_auth):
        api = make_api(mock_auth)
        with pytest.raises(RuntimeError, match="not initialized"):
            await api.get_devices()

    async def test_returns_devices_after_initialization(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        mock_device = MagicMock(spec=LGHorizonDevice)
        api._devices = {"device-1": mock_device}
        devices = await api.get_devices()
        assert devices == {"device-1": mock_device}


# ---------------------------------------------------------------------------
# get_profiles()
# ---------------------------------------------------------------------------


class TestGetProfiles:
    async def test_raises_if_not_initialized(self, mock_auth):
        api = make_api(mock_auth)
        with pytest.raises(RuntimeError, match="not initialized"):
            await api.get_profiles()

    async def test_returns_profiles_after_initialization(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        profiles = await api.get_profiles()
        assert "profile-1" in profiles
        assert "profile-2" in profiles


# ---------------------------------------------------------------------------
# has_cloud_recording property
# ---------------------------------------------------------------------------


class TestHasCloudRecording:
    def test_raises_if_not_initialized(self, mock_auth):
        api = make_api(mock_auth)
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = api.has_cloud_recording

    def test_returns_true_when_recording_retention_set(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        # sample_customer_json has recordingRetentionPeriod=365
        assert api.has_cloud_recording is True

    def test_returns_false_when_no_recording_retention(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        no_recording_json = {**sample_customer_json, "recordingRetentionPeriod": 0}
        api = make_api(mock_auth)
        api._initialized = True
        api._customer = LGHorizonCustomer(no_recording_json)
        api._channels = {}
        api._mqtt_client = MagicMock()
        assert api.has_cloud_recording is False


# ---------------------------------------------------------------------------
# get_profile_channels()
# ---------------------------------------------------------------------------


class TestGetProfileChannels:
    async def test_returns_favorite_channels_for_profile_with_favorites(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        """profile-1 has channel-1 as favourite — must return only channel-1."""
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        channels = await api.get_profile_channels("profile-1")
        assert "channel-1" in channels
        assert len(channels) == 1

    async def test_returns_all_channels_if_profile_has_no_favorites(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        """profile-2 has an empty favoriteChannels list — must return all channels."""
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        # Add an extra channel so "all channels" is more than what profile-1 would return
        extra_channel_json = {
            "id": "channel-2",
            "name": "NPO 2",
            "logicalChannelNumber": "2",
            "isRadio": False,
            "replayPrePadding": 0,
            "replayPostPadding": 0,
            "logo": {"focused": ""},
            "imageStream": {"full": ""},
            "linearProducts": [],
        }
        api._channels["channel-2"] = LGHorizonChannel(extra_channel_json)
        channels = await api.get_profile_channels("profile-2")
        assert "channel-1" in channels
        assert "channel-2" in channels

    async def test_falls_back_to_first_profile_if_profile_id_not_found(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        """Unknown profile_id → fall back to first profile (profile-1 with favorites)."""
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        channels = await api.get_profile_channels("nonexistent-profile")
        # Falls back to profile-1 which has channel-1 as favourite
        assert "channel-1" in channels

    async def test_returns_all_channels_if_no_profiles_exist(
        self, mock_auth, sample_channel_json
    ):
        """Customer with no profiles → return all channels."""
        no_profiles_json = {
            "customerId": "cust-x",
            "hashedCustomerId": "hashed-x",
            "countryId": "nl",
            "cityId": 9999,
            "assignedDevices": [],
            "profiles": [],
        }
        api = make_api(mock_auth)
        api._initialized = True
        api._customer = LGHorizonCustomer(no_profiles_json)
        api._channels = {"channel-1": LGHorizonChannel(sample_channel_json)}
        api._mqtt_client = MagicMock()
        channels = await api.get_profile_channels("profile-1")
        assert "channel-1" in channels


# ---------------------------------------------------------------------------
# get_all_recordings()
# ---------------------------------------------------------------------------


class TestGetAllRecordings:
    async def test_returns_empty_list_if_no_cloud_recording(
        self, mock_auth, sample_channel_json
    ):
        no_recording_json = {
            "customerId": "cust-x",
            "hashedCustomerId": "hashed-x",
            "countryId": "nl",
            "cityId": 9999,
            "assignedDevices": [],
            "profiles": [],
            "recordingRetentionPeriod": 0,
        }
        api = make_api(mock_auth)
        api._initialized = True
        api._customer = LGHorizonCustomer(no_recording_json)
        result = await api.get_all_recordings()
        assert isinstance(result, LGHorizonRecordingList)
        # No cloud recording → recording service should NOT have been called
        mock_auth.request.assert_not_called()

    async def test_calls_recording_service_when_cloud_recording_available(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        # Provide a service config mock so get_service_url works
        service_config = MagicMock()
        service_config.get_service_url = MagicMock(return_value="https://recording.example.com")
        api._service_config = service_config

        recordings_payload = {"recordings": [], "total": 0}
        mock_auth.request = AsyncMock(return_value=recordings_payload)

        with patch.object(
            api._recording_factory, "create_recordings", new=AsyncMock(return_value=LGHorizonRecordingList([]))
        ):
            result = await api.get_all_recordings()

        mock_auth.request.assert_called_once()
        assert isinstance(result, LGHorizonRecordingList)


# ---------------------------------------------------------------------------
# get_recording_quota()
# ---------------------------------------------------------------------------


class TestGetRecordingQuota:
    async def test_returns_empty_quota_if_no_cloud_recording(self, mock_auth):
        no_recording_json = {
            "customerId": "cust-x",
            "hashedCustomerId": "hashed-x",
            "countryId": "nl",
            "cityId": 9999,
            "assignedDevices": [],
            "profiles": [],
            "recordingRetentionPeriod": 0,
        }
        api = make_api(mock_auth)
        api._initialized = True
        api._customer = LGHorizonCustomer(no_recording_json)
        result = await api.get_recording_quota()
        assert isinstance(result, LGHorizonRecordingQuota)
        mock_auth.request.assert_not_called()

    async def test_calls_quota_api_when_cloud_recording_available(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        service_config = MagicMock()
        service_config.get_service_url = MagicMock(return_value="https://recording.example.com")
        api._service_config = service_config

        quota_payload = {"used": 10, "total": 100}
        mock_auth.request = AsyncMock(return_value=quota_payload)

        result = await api.get_recording_quota()
        mock_auth.request.assert_called_once()
        assert isinstance(result, LGHorizonRecordingQuota)


# ---------------------------------------------------------------------------
# _on_mqtt_message()
# ---------------------------------------------------------------------------


def _make_mock_device(state=LGHorizonRunningState.ONLINE_RUNNING):
    device = MagicMock(spec=LGHorizonDevice)
    device.handle_status_message = AsyncMock()
    device.handle_ui_status_message = AsyncMock()
    device.device_state = MagicMock()
    device.device_state.state = state
    return device


class TestOnMqttMessage:
    async def test_routes_status_message_to_correct_device(
        self, mock_auth, sample_customer_json, sample_channel_json, sample_status_payload
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        mock_device = _make_mock_device()
        api._devices = {"device-1": mock_device}

        status_msg = MagicMock(spec=LGHorizonStatusMessage)
        status_msg.message_type = LGHorizonMessageType.STATUS
        status_msg.source = "device-1"

        with patch.object(
            api._message_factory, "create_message", new=AsyncMock(return_value=status_msg)
        ):
            await api._on_mqtt_message(sample_status_payload, "household-123/device-1/status")

        mock_device.handle_status_message.assert_awaited_once_with(status_msg)
        mock_device.handle_ui_status_message.assert_not_awaited()

    async def test_routes_ui_status_message_to_correct_device(
        self, mock_auth, sample_customer_json, sample_channel_json, sample_ui_status_payload
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        mock_device = _make_mock_device(state=LGHorizonRunningState.ONLINE_RUNNING)
        api._devices = {"device-1": mock_device}

        ui_msg = MagicMock(spec=LGHorizonUIStatusMessage)
        ui_msg.message_type = LGHorizonMessageType.UI_STATUS
        ui_msg.source = "device-1"

        with patch.object(
            api._message_factory, "create_message", new=AsyncMock(return_value=ui_msg)
        ):
            await api._on_mqtt_message(sample_ui_status_payload, "household-123/device-1/uistatus")

        mock_device.handle_ui_status_message.assert_awaited_once_with(ui_msg)
        mock_device.handle_status_message.assert_not_awaited()

    async def test_ignores_status_message_for_unknown_device(
        self, mock_auth, sample_customer_json, sample_channel_json, sample_status_payload
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        mock_device = _make_mock_device()
        api._devices = {"device-1": mock_device}

        status_msg = MagicMock(spec=LGHorizonStatusMessage)
        status_msg.message_type = LGHorizonMessageType.STATUS
        status_msg.source = "unknown-device"

        with patch.object(
            api._message_factory, "create_message", new=AsyncMock(return_value=status_msg)
        ):
            await api._on_mqtt_message(sample_status_payload, "household-123/unknown-device/status")

        mock_device.handle_status_message.assert_not_awaited()

    async def test_ignores_ui_status_if_device_not_online_running(
        self, mock_auth, sample_customer_json, sample_channel_json, sample_ui_status_payload
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        mock_device = _make_mock_device(state=LGHorizonRunningState.OFFLINE)
        api._devices = {"device-1": mock_device}

        ui_msg = MagicMock(spec=LGHorizonUIStatusMessage)
        ui_msg.message_type = LGHorizonMessageType.UI_STATUS
        ui_msg.source = "device-1"

        with patch.object(
            api._message_factory, "create_message", new=AsyncMock(return_value=ui_msg)
        ):
            await api._on_mqtt_message(sample_ui_status_payload, "household-123/device-1/uistatus")

        mock_device.handle_ui_status_message.assert_not_awaited()


# ---------------------------------------------------------------------------
# disconnect()
# ---------------------------------------------------------------------------


class TestDisconnect:
    async def test_calls_mqtt_client_disconnect(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        await api.disconnect()
        api._mqtt_client.disconnect.assert_awaited_once()

    async def test_sets_initialized_to_false(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        assert api._initialized is True
        await api.disconnect()
        assert api._initialized is False

    async def test_disconnect_without_mqtt_client_does_not_raise(self, mock_auth):
        api = make_api(mock_auth)
        api._initialized = True
        # _mqtt_client is None — must not raise
        await api.disconnect()
        assert api._initialized is False
