"""Unit tests for LGHorizonDeviceStateProcessor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lghorizon.lghorizon_device_state_processor import LGHorizonDeviceStateProcessor
from lghorizon.lghorizon_models import (
    LGHorizonChannel,
    LGHorizonCustomer,
    LGHorizonDeviceState,
    LGHorizonMediaType,
    LGHorizonRunningState,
    LGHorizonSourceType,
    LGHorizonStatusMessage,
    LGHorizonUIStateType,
    LGHorizonUIStatusMessage,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers / shared setup
# ---------------------------------------------------------------------------

PROFILE_ID = "profile-1"
TOPIC = "some/topic"


@pytest.fixture
def channel(sample_channel_json):
    return LGHorizonChannel(sample_channel_json)


@pytest.fixture
def channels(channel):
    return {"channel-1": channel}


@pytest.fixture
def customer(sample_customer_json):
    return LGHorizonCustomer(sample_customer_json)


@pytest.fixture
def mock_service_config():
    """Return a mock service config whose get_service_url is a MagicMock."""
    config = MagicMock()
    config.get_service_url = MagicMock(return_value="https://service.example.com")
    return config


@pytest.fixture
def processor(mock_auth, channels, customer, mock_service_config):
    mock_auth.get_service_config = AsyncMock(return_value=mock_service_config)
    return LGHorizonDeviceStateProcessor(mock_auth, channels, customer, PROFILE_ID)


# ---------------------------------------------------------------------------
# process_state tests
# ---------------------------------------------------------------------------


class TestProcessState:
    async def test_sets_running_state_online_running(self, processor):
        device_state = LGHorizonDeviceState()
        payload = {"source": "device-1", "state": "ONLINE_RUNNING"}
        msg = LGHorizonStatusMessage(payload, TOPIC)

        await processor.process_state(device_state, msg)

        assert device_state.state == LGHorizonRunningState.ONLINE_RUNNING

    async def test_sets_running_state_online_standby(self, processor):
        device_state = LGHorizonDeviceState()
        payload = {"source": "device-1", "state": "ONLINE_STANDBY"}
        msg = LGHorizonStatusMessage(payload, TOPIC)

        await processor.process_state(device_state, msg)

        assert device_state.state == LGHorizonRunningState.ONLINE_STANDBY

    async def test_sets_running_state_offline(self, processor):
        device_state = LGHorizonDeviceState()
        payload = {"source": "device-1", "state": "OFFLINE"}
        msg = LGHorizonStatusMessage(payload, TOPIC)

        await processor.process_state(device_state, msg)

        assert device_state.state == LGHorizonRunningState.OFFLINE

    async def test_sets_running_state_offline_network_standby(self, processor):
        device_state = LGHorizonDeviceState()
        payload = {"source": "device-1", "state": "OFFLINE_NETWORK_STANDBY"}
        msg = LGHorizonStatusMessage(payload, TOPIC)

        await processor.process_state(device_state, msg)

        assert device_state.state == LGHorizonRunningState.OFFLINE_NETWORK_STANDBY

    async def test_resets_device_state_before_setting(self, processor):
        """Existing state should be wiped before the new state is applied."""
        device_state = LGHorizonDeviceState()
        # Pre-populate some fields
        device_state.channel_id = "old-channel"
        device_state.show_title = "Old Show"

        payload = {"source": "device-1", "state": "ONLINE_RUNNING"}
        msg = LGHorizonStatusMessage(payload, TOPIC)

        await processor.process_state(device_state, msg)

        assert device_state.channel_id is None
        assert device_state.show_title is None
        assert device_state.state == LGHorizonRunningState.ONLINE_RUNNING

    @pytest.mark.parametrize(
        "state_str",
        ["ONLINE_RUNNING", "ONLINE_STANDBY", "OFFLINE_NETWORK_STANDBY", "OFFLINE", "UNKNOWN"],
    )
    async def test_all_running_states(self, processor, state_str):
        device_state = LGHorizonDeviceState()
        payload = {"source": "device-1", "state": state_str}
        msg = LGHorizonStatusMessage(payload, TOPIC)

        await processor.process_state(device_state, msg)

        assert device_state.state == LGHorizonRunningState[state_str]


# ---------------------------------------------------------------------------
# process_ui_state tests
# ---------------------------------------------------------------------------


class TestProcessUiState:
    def _make_ui_msg(self, status_dict):
        payload = {
            "source": "device-1",
            "messageTimeStamp": 1700000000,
            "status": status_dict,
        }
        return LGHorizonUIStatusMessage(payload, TOPIC)

    def _make_ui_msg_no_status(self):
        payload = {"source": "device-1", "messageTimeStamp": 1700000000}
        return LGHorizonUIStatusMessage(payload, TOPIC)

    async def test_returns_early_if_ui_state_is_none(self, processor):
        """If the payload has no 'status' key, ui_state is None and we bail early."""
        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_RUNNING
        msg = self._make_ui_msg_no_status()

        await processor.process_ui_state(device_state, msg)

        # State was reset (channel_id still None) and nothing further set
        assert device_state.channel_id is None
        assert device_state.show_title is None

    async def test_returns_early_if_device_in_standby(self, processor):
        """Device in ONLINE_STANDBY should short-circuit without processing content."""
        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_STANDBY

        status_dict = {
            "uiStatus": "mainUI",
            "playerState": {
                "sourceType": "linear",
                "speed": 1,
                "source": {"channelId": "channel-1", "eventId": "event-1"},
            },
        }
        msg = self._make_ui_msg(status_dict)

        await processor.process_ui_state(device_state, msg)

        assert device_state.channel_id is None

    async def test_returns_early_if_player_state_none_for_mainui(self, processor):
        """MAINUI with no playerState should return early without setting content."""
        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_RUNNING

        status_dict = {"uiStatus": "mainUI"}  # no playerState key
        msg = self._make_ui_msg(status_dict)

        await processor.process_ui_state(device_state, msg)

        assert device_state.channel_id is None
        assert device_state.show_title is None

    async def test_routes_apps_to_process_apps_state(self, processor):
        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_RUNNING

        status_dict = {
            "uiStatus": "apps",
            "appsState": {
                "id": "netflix",
                "appName": "Netflix",
                "logoPath": "https://example.com/netflix.png",
            },
        }
        msg = self._make_ui_msg(status_dict)

        await processor.process_ui_state(device_state, msg)

        assert device_state.id == "netflix"
        assert device_state.show_title == "Netflix"
        assert device_state.image == "https://example.com/netflix.png"
        assert device_state.ui_state_type == LGHorizonUIStateType.APPS
        assert device_state.media_type == LGHorizonMediaType.APP

    async def test_routes_mainui_to_process_main_ui_state(
        self, processor, mock_auth, sample_replay_event_json, mock_service_config
    ):
        """MAINUI with a linear playerState should trigger _process_linear_state."""
        mock_auth.get_service_config = AsyncMock(return_value=mock_service_config)
        mock_auth.request = AsyncMock(return_value=sample_replay_event_json)

        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_RUNNING

        status_dict = {
            "uiStatus": "mainUI",
            "playerState": {
                "sourceType": "linear",
                "speed": 1,
                "lastSpeedChangeTime": 1700000000000,
                "relativePosition": 60000,
                "source": {"channelId": "channel-1", "eventId": "event-1"},
            },
        }
        msg = self._make_ui_msg(status_dict)

        await processor.process_ui_state(device_state, msg)

        assert device_state.ui_state_type == LGHorizonUIStateType.MAINUI


# ---------------------------------------------------------------------------
# _process_apps_state (via process_ui_state)
# ---------------------------------------------------------------------------


class TestProcessAppsState:
    async def test_sets_all_app_fields(self, processor):
        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_RUNNING

        payload = {
            "source": "device-1",
            "messageTimeStamp": 1700000000,
            "status": {
                "uiStatus": "apps",
                "appsState": {
                    "id": "youtube",
                    "appName": "YouTube",
                    "logoPath": "https://example.com/youtube.png",
                },
            },
        }
        msg = LGHorizonUIStatusMessage(payload, TOPIC)

        await processor.process_ui_state(device_state, msg)

        assert device_state.id == "youtube"
        assert device_state.show_title == "YouTube"
        assert device_state.image == "https://example.com/youtube.png"
        assert device_state.ui_state_type == LGHorizonUIStateType.APPS
        assert device_state.media_type == LGHorizonMediaType.APP


# ---------------------------------------------------------------------------
# _process_linear_state (via process_ui_state with mocked API)
# ---------------------------------------------------------------------------


class TestProcessLinearState:
    def _linear_ui_msg(self):
        payload = {
            "source": "device-1",
            "messageTimeStamp": 1700000000,
            "status": {
                "uiStatus": "mainUI",
                "playerState": {
                    "sourceType": "linear",
                    "speed": 1,
                    "lastSpeedChangeTime": 1700000000000,
                    "relativePosition": 60000,
                    "source": {"channelId": "channel-1", "eventId": "event-1"},
                },
            },
        }
        return LGHorizonUIStatusMessage(payload, TOPIC)

    async def test_populates_channel_and_show_info(
        self, processor, mock_auth, sample_replay_event_json, mock_service_config
    ):
        mock_auth.get_service_config = AsyncMock(return_value=mock_service_config)
        mock_auth.request = AsyncMock(return_value=sample_replay_event_json)

        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_RUNNING

        await processor.process_ui_state(device_state, self._linear_ui_msg())

        assert device_state.channel_id == "channel-1"
        assert device_state.channel_name == "NPO 1"
        assert device_state.show_title == "Test Show"
        assert device_state.episode_title == "Pilot"
        assert device_state.season_number == 1
        assert device_state.episode_number == 1
        assert device_state.source_type == LGHorizonSourceType.LINEAR
        assert device_state.media_type == LGHorizonMediaType.CHANNEL
        # image should contain the channel stream image URL
        assert "https://example.com/stream.png" in device_state.image

    async def test_sets_start_end_duration(
        self, processor, mock_auth, sample_replay_event_json, mock_service_config
    ):
        mock_auth.get_service_config = AsyncMock(return_value=mock_service_config)
        mock_auth.request = AsyncMock(return_value=sample_replay_event_json)

        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_RUNNING

        await processor.process_ui_state(device_state, self._linear_ui_msg())

        assert device_state.start_time == 1700000000
        assert device_state.end_time == 1700003600
        assert device_state.duration == 3600


# ---------------------------------------------------------------------------
# _process_vod_state (via process_ui_state with mocked API)
# ---------------------------------------------------------------------------


class TestProcessVodState:
    def _vod_ui_msg(self, title_id="vod-1"):
        payload = {
            "source": "device-1",
            "messageTimeStamp": 1700000000,
            "status": {
                "uiStatus": "mainUI",
                "playerState": {
                    "sourceType": "VOD",
                    "speed": 1,
                    "lastSpeedChangeTime": 1700000000000,
                    "relativePosition": 120000,
                    "source": {"titleId": title_id},
                },
            },
        }
        return LGHorizonUIStatusMessage(payload, TOPIC)

    def _intents_response(self, image_url="https://example.com/vod_image.png"):
        return [{"intents": [{"url": image_url}]}]

    async def test_episode_type_sets_series_and_episode_fields(
        self, processor, mock_auth, sample_vod_json, mock_service_config
    ):
        mock_auth.get_service_config = AsyncMock(return_value=mock_service_config)
        mock_auth.request = AsyncMock(
            side_effect=[sample_vod_json, self._intents_response()]
        )

        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_RUNNING

        await processor.process_ui_state(device_state, self._vod_ui_msg())

        assert device_state.id == "vod-1"
        assert device_state.show_title == "Series Title"
        assert device_state.episode_title == "Episode Title"
        assert device_state.season_number == 3
        assert device_state.episode_number == 7
        assert device_state.media_type == LGHorizonMediaType.EPISODE

    async def test_asset_type_sets_movie_fields(
        self, processor, mock_auth, mock_service_config
    ):
        asset_vod_json = {
            "id": "vod-movie-1",
            "type": "ASSET",
            "title": "Great Movie",
            "duration": 5400.0,
        }
        mock_auth.get_service_config = AsyncMock(return_value=mock_service_config)
        mock_auth.request = AsyncMock(
            side_effect=[asset_vod_json, self._intents_response()]
        )

        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_RUNNING

        await processor.process_ui_state(device_state, self._vod_ui_msg("vod-movie-1"))

        assert device_state.id == "vod-movie-1"
        assert device_state.show_title == "Great Movie"
        assert device_state.episode_title is None
        assert device_state.media_type == LGHorizonMediaType.MOVIE

    async def test_duration_and_position_set(
        self, processor, mock_auth, sample_vod_json, mock_service_config
    ):
        mock_auth.get_service_config = AsyncMock(return_value=mock_service_config)
        mock_auth.request = AsyncMock(
            side_effect=[sample_vod_json, self._intents_response()]
        )

        device_state = LGHorizonDeviceState()
        device_state.state = LGHorizonRunningState.ONLINE_RUNNING

        await processor.process_ui_state(device_state, self._vod_ui_msg())

        assert device_state.duration == 2700.0
        # relativePosition 120000 ms → 120 s
        assert device_state.position == 120
