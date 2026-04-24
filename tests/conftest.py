"""Shared fixtures for LG Horizon tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession

from lghorizon.lghorizon_models import (
    LGHorizonAuth,
    LGHorizonChannel,
    LGHorizonCustomer,
    LGHorizonServicesConfig,
)


@pytest.fixture
def sample_channel_json():
    """Sample channel JSON payload."""
    return {
        "id": "channel-1",
        "name": "NPO 1",
        "logicalChannelNumber": "1",
        "isRadio": False,
        "replayPrePadding": 10,
        "replayPostPadding": 5,
        "logo": {"focused": "https://example.com/logo.png"},
        "imageStream": {"full": "https://example.com/stream.png"},
        "linearProducts": ["product-1", "product-2"],
    }


@pytest.fixture
def sample_customer_json():
    """Sample customer JSON payload."""
    return {
        "customerId": "cust-123",
        "hashedCustomerId": "hashed-cust-123",
        "countryId": "nl",
        "cityId": 1234,
        "recordingRetentionPeriod": 365,
        "assignedDevices": [
            {
                "deviceId": "device-1",
                "hashedCPEId": "hashed-cpe-1",
                "platformType": "EOS",
                "settings": {"deviceFriendlyName": "Living Room"},
            }
        ],
        "profiles": [
            {
                "profileId": "profile-1",
                "name": "Main",
                "favoriteChannels": ["channel-1"],
                "options": {"lang": "nl"},
            },
            {
                "profileId": "profile-2",
                "name": "Kids",
                "favoriteChannels": [],
                "options": {"lang": "en"},
            },
        ],
    }


@pytest.fixture
def sample_service_config():
    """Sample service configuration."""
    return LGHorizonServicesConfig(
        {
            "linearService": {"URL": "https://linear.example.com"},
            "recordingService": {"URL": "https://recording.example.com"},
            "personalizationService": {"URL": "https://personal.example.com"},
            "purchaseService": {"URL": "https://purchase.example.com"},
            "vodService": {"URL": "https://vod.example.com"},
            "imageService": {"URL": "https://image.example.com"},
            "authorizationService": {"URL": "https://auth.example.com"},
            "mqttBroker": {"URL": "wss://mqtt.example.com:443/mqtt"},
        }
    )


@pytest.fixture
def mock_auth():
    """Create a mock LGHorizonAuth."""
    auth = MagicMock(spec=LGHorizonAuth)
    auth.household_id = "household-123"
    auth.country_code = "nl"
    auth.request = AsyncMock()
    auth.get_service_config = AsyncMock()
    auth.get_mqtt_token = AsyncMock(return_value="mqtt-token-123")
    auth.fetch_access_token = AsyncMock()
    return auth


@pytest.fixture
def sample_replay_event_json():
    """Sample replay event JSON."""
    return {
        "eventId": "event-1",
        "channelId": "channel-1",
        "title": "Test Show",
        "episodeName": "Pilot",
        "seasonNumber": 1,
        "episodeNumber": 1,
        "startTime": 1700000000,
        "endTime": 1700003600,
    }


@pytest.fixture
def sample_recording_single_json():
    """Sample single recording JSON."""
    return {
        "id": "rec-1",
        "type": "single",
        "title": "Test Recording",
        "channelId": "channel-1",
        "recordingState": "recorded",
        "source": "show",
        "episodeTitle": "Episode 1",
        "episodeId": "ep-1",
        "seasonNumber": 2,
        "episodeNumber": 5,
        "showId": "show-1",
        "showTitle": "Test Show",
        "seasonId": "season-2",
        "duration": 3600,
        "startTime": "2024-01-15T20:00:00Z",
        "endTime": "2024-01-15T21:00:00Z",
        "poster": {"url": "https://example.com/poster.png"},
    }


@pytest.fixture
def sample_recording_season_json():
    """Sample season recording JSON."""
    return {
        "id": "rec-season-1",
        "type": "season",
        "title": "Test Show",
        "channelId": "channel-1",
        "recordingState": "recorded",
        "source": "show",
        "noOfEpisodes": 10,
        "seasonTitle": "Season 1",
        "showId": "show-1",
        "mostRelevantEpisode": {
            "recordingState": "recorded",
            "seasonNumber": 1,
            "episodeNumber": 3,
        },
    }


@pytest.fixture
def sample_recording_show_json():
    """Sample show recording JSON."""
    return {
        "id": "rec-show-1",
        "type": "show",
        "title": "Test Show",
        "channelId": "channel-1",
        "recordingState": "recorded",
        "source": "show",
        "noOfEpisodes": 25,
        "mostRelevantEpisode": {
            "recordingState": "recorded",
            "seasonNumber": 2,
            "episodeNumber": 1,
        },
    }


@pytest.fixture
def sample_status_payload():
    """Sample MQTT status message payload."""
    return {
        "source": "device-1",
        "state": "ONLINE_RUNNING",
        "deviceType": "STB",
    }


@pytest.fixture
def sample_ui_status_payload():
    """Sample MQTT UI status message payload."""
    return {
        "source": "device-1",
        "messageTimeStamp": 1700000000,
        "type": "CPE.uiStatus",
        "status": {
            "uiStatus": "mainUI",
            "playerState": {
                "sourceType": "linear",
                "speed": 1,
                "lastSpeedChangeTime": 1700000000000,
                "relativePosition": 60000,
                "source": {
                    "channelId": "channel-1",
                    "eventId": "event-1",
                },
            },
        },
    }


@pytest.fixture
def sample_vod_json():
    """Sample VOD JSON payload."""
    return {
        "id": "vod-1",
        "type": "EPISODE",
        "title": "Episode Title",
        "seriesTitle": "Series Title",
        "season": 3,
        "episode": 7,
        "duration": 2700.0,
    }
