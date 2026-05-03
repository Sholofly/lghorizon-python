"""Unit tests for LGHorizonApi."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lghorizon.lghorizon_api import LGHorizonApi
from lghorizon.lghorizon_device import LGHorizonDevice
from lghorizon.lghorizon_models import (
    LGHorizonAuth,
    LGHorizonChannel,
    LGHorizonEntitlements,
    LGHorizonCustomer,
    LGHorizonEpg,
    LGHorizonEventDetail,
    LGHorizonManagedRecordingList,
    LGHorizonMessageType,
    LGHorizonReplayChannel,
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
# has_pvr / has_local_dvr properties
# ---------------------------------------------------------------------------


class TestHasPvr:
    def test_raises_if_not_initialized(self, mock_auth):
        api = make_api(mock_auth)
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = api.has_pvr

    def test_returns_true_when_pvr_feature_present(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        api._entitlements = LGHorizonEntitlements({"features": ["PVR", "LOCALDVR"]})
        assert api.has_pvr is True

    def test_returns_false_when_pvr_feature_absent(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        api._entitlements = LGHorizonEntitlements({"features": ["LOCALDVR"]})
        assert api.has_pvr is False


class TestHasLocalDvr:
    def test_raises_if_not_initialized(self, mock_auth):
        api = make_api(mock_auth)
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = api.has_local_dvr

    def test_returns_true_when_localdvr_feature_present(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        api._entitlements = LGHorizonEntitlements({"features": ["LOCALDVR"]})
        assert api.has_local_dvr is True

    def test_returns_false_when_localdvr_feature_absent(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        api._entitlements = LGHorizonEntitlements({"features": ["PVR"]})
        assert api.has_local_dvr is False


# ---------------------------------------------------------------------------
# has_recording property
# ---------------------------------------------------------------------------


class TestHasRecording:
    def test_raises_if_not_initialized(self, mock_auth):
        api = make_api(mock_auth)
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = api.has_recording

    def test_returns_true_when_pvr_feature_present(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        api._entitlements = LGHorizonEntitlements({"features": ["PVR"]})
        assert api.has_recording is True

    def test_returns_true_when_localdvr_feature_present(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        api._entitlements = LGHorizonEntitlements({"features": ["LOCALDVR"]})
        assert api.has_recording is True

    def test_returns_false_when_no_recording_features(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        api._entitlements = LGHorizonEntitlements({"features": []})
        assert api.has_recording is False


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
    async def test_returns_empty_list_if_no_recording_entitlement(
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
        api._entitlements = LGHorizonEntitlements({"features": []})
        result = await api.get_all_recordings()
        assert isinstance(result, LGHorizonRecordingList)
        # No recording entitlement → recording service should NOT have been called
        mock_auth.request.assert_not_called()

    async def test_calls_recording_service_when_cloud_recording_available(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        api._entitlements = LGHorizonEntitlements({"features": ["PVR"]})
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
    async def test_returns_empty_quota_if_no_recording_entitlement(self, mock_auth):
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
        api._entitlements = LGHorizonEntitlements({"features": []})
        result = await api.get_recording_quota()
        assert isinstance(result, LGHorizonRecordingQuota)
        mock_auth.request.assert_not_called()

    async def test_calls_quota_api_when_cloud_recording_available(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        api._entitlements = LGHorizonEntitlements({"features": ["PVR"]})
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
        mock_device = _make_mock_device()
        api._devices = {"device-1": mock_device}
        mock_device.device_state.state = LGHorizonRunningState.ONLINE_RUNNING

        ui_msg = MagicMock(spec=LGHorizonUIStatusMessage)
        ui_msg.message_type = LGHorizonMessageType.UI_STATUS
        ui_msg.source = "device-1"

        with patch.object(
            api._message_factory, "create_message", new=AsyncMock(return_value=ui_msg)
        ):
            await api._on_mqtt_message(sample_ui_status_payload, "household-123/device-1/uistatus")

        mock_device.handle_ui_status_message.assert_awaited_once_with(ui_msg)
        mock_device.handle_status_message.assert_not_awaited()

    async def test_routes_capacity_message_to_correct_device(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        mock_device = MagicMock(spec=LGHorizonDevice)
        mock_device.update_local_recording_capacity = AsyncMock()
        api._devices = {"device-1": mock_device}
        payload = {"type": "CPE.capacity", "source": "device-1", "used": 50}
        await api._on_mqtt_message(payload, "household-123/device-1")
        mock_device.update_local_recording_capacity.assert_awaited_once_with(payload)

    async def test_ignores_capacity_message_for_unknown_device(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        api._devices = {}
        payload = {"type": "CPE.capacity", "source": "unknown-device", "used": 50}
        # Should not raise
        await api._on_mqtt_message(payload, "household-123/unknown-device")

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


# ---------------------------------------------------------------------------
# get_epg()
# ---------------------------------------------------------------------------


class TestGetEpg:
    def _make_api(self, mock_auth, sample_customer_json, sample_channel_json):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        service_config = MagicMock()
        service_config.get_service_url = MagicMock(return_value="https://epg.example.com")
        api._service_config = service_config
        return api

    async def test_returns_lghorizonepg_with_merged_segments(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = self._make_api(mock_auth, sample_customer_json, sample_channel_json)

        segment_response = {
            "entries": [
                {"channelId": "NL_001", "events": [{"id": "e1", "title": "Show1"}]},
            ]
        }
        mock_auth.request = AsyncMock(return_value=segment_response)

        from datetime import date
        result = await api.get_epg(epg_date=date(2026, 4, 24))

        assert isinstance(result, LGHorizonEpg)
        # 4 segments requested, each returning 1 entry for NL_001 — they should merge
        assert mock_auth.request.call_count == 4
        events = result.get_channel_events("NL_001")
        # 4 segments × 1 event = 4 events merged
        assert len(events) == 4

    async def test_returns_empty_epg_when_all_segments_fail(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = self._make_api(mock_auth, sample_customer_json, sample_channel_json)
        mock_auth.request = AsyncMock(side_effect=Exception("network error"))

        from datetime import date
        result = await api.get_epg(epg_date=date(2026, 4, 24))

        assert isinstance(result, LGHorizonEpg)
        assert result.entries == []

    async def test_defaults_to_today_when_no_date_given(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = self._make_api(mock_auth, sample_customer_json, sample_channel_json)
        mock_auth.request = AsyncMock(return_value={"entries": []})

        from datetime import date
        with patch("lghorizon.lghorizon_api.date_type") as _mock_date:
            # Just verify it runs without raising and returns LGHorizonEpg
            result = await api.get_epg()
        assert isinstance(result, LGHorizonEpg)


# ---------------------------------------------------------------------------
# get_event_detail()
# ---------------------------------------------------------------------------


class TestGetEventDetail:
    async def test_returns_lghorizoneventdetail(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        service_config = MagicMock()
        service_config.get_service_url = MagicMock(return_value="https://linear.example.com")
        api._service_config = service_config

        detail_payload = {
            "eventId": "e1",
            "channelId": "CH1",
            "title": "Movie Title",
        }
        mock_auth.request = AsyncMock(return_value=detail_payload)

        result = await api.get_event_detail("e1")

        assert isinstance(result, LGHorizonEventDetail)
        assert result.event_id == "e1"
        assert result.title == "Movie Title"
        mock_auth.request.assert_called_once()


# ---------------------------------------------------------------------------
# get_replay_channels()
# ---------------------------------------------------------------------------


class TestGetReplayChannels:
    async def test_returns_list_of_replay_channels(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        service_config = MagicMock()
        service_config.get_service_url = MagicMock(return_value="https://replay.example.com")
        api._service_config = service_config

        channels_payload = {
            "replayChannels": [
                {"id": "NL_001", "name": "NPO 1", "logo": "http://logo1.png"},
                {"id": "NL_002", "name": "NPO 2", "logo": "http://logo2.png"},
            ]
        }
        mock_auth.request = AsyncMock(return_value=channels_payload)

        result = await api.get_replay_channels()

        assert isinstance(result, list)
        assert len(result) == 2
        for ch in result:
            assert isinstance(ch, LGHorizonReplayChannel)
        assert result[0].id == "NL_001"
        assert result[1].name == "NPO 2"
        mock_auth.request.assert_called_once()


# ---------------------------------------------------------------------------
# get_managed_recordings()
# ---------------------------------------------------------------------------


class TestGetManagedRecordings:
    async def test_returns_managed_recording_list(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        service_config = MagicMock()
        service_config.get_service_url = MagicMock(return_value="https://recmgmt.example.com")
        api._service_config = service_config

        recordings_payload = {
            "total": 2,
            "limit": 500,
            "offset": 0,
            "data": [
                {"id": "r1", "diskSpace": 0.5},
                {"id": "r2", "diskSpace": 1.0},
            ],
        }
        mock_auth.request = AsyncMock(return_value=recordings_payload)

        result = await api.get_managed_recordings()

        assert isinstance(result, LGHorizonManagedRecordingList)
        assert result.total == 2
        assert len(result.recordings) == 2
        mock_auth.request.assert_called_once()

    async def test_passes_limit_and_offset_params(
        self, mock_auth, sample_customer_json, sample_channel_json
    ):
        api = make_initialized_api(mock_auth, sample_customer_json, sample_channel_json)
        service_config = MagicMock()
        service_config.get_service_url = MagicMock(return_value="https://recmgmt.example.com")
        api._service_config = service_config

        mock_auth.request = AsyncMock(return_value={"total": 0, "limit": 10, "offset": 20, "data": []})

        await api.get_managed_recordings(limit=10, offset=20)

        call_args = mock_auth.request.call_args
        # Second positional arg is the path
        path = call_args[0][1]
        assert "limit=10" in path
        assert "offset=20" in path
