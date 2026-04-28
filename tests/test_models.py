"""Comprehensive unit tests for lghorizon/lghorizon_models.py."""

from __future__ import annotations

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call

from lghorizon.lghorizon_models import (
    LGHorizonAdBreak,
    LGHorizonAppsState,
    LGHorizonChannel,
    LGHorizonCustomer,
    LGHorizonDeviceState,
    LGHorizonEntitlements,
    LGHorizonEpg,
    LGHorizonEpgEntry,
    LGHorizonEpgEvent,
    LGHorizonEventDetail,
    LGHorizonLinearSource,
    LGHorizonManagedRecording,
    LGHorizonManagedRecordingList,
    LGHorizonMediaType,
    LGHorizonMessageType,
    LGHorizonNDVRSource,
    LGHorizonPlayerState,
    LGHorizonProfile,
    LGHorizonReplayChannel,
    LGHorizonReplayEvent,
    LGHorizonReplaySource,
    LGHorizonRecordingList,
    LGHorizonRecordingQuota,
    LGHorizonRecordingSeason,
    LGHorizonRecordingShow,
    LGHorizonRecordingSingle,
    LGHorizonRecordingSource,
    LGHorizonRecordingState,
    LGHorizonRecordingType,
    LGHorizonReviewBufferSource,
    LGHorizonRunningState,
    LGHorizonServicesConfig,
    LGHorizonShowRecordingList,
    LGHorizonSourceType,
    LGHorizonStatusMessage,
    LGHorizonUIState,
    LGHorizonUIStateType,
    LGHorizonUIStatusMessage,
    LGHorizonUnknownMessage,
    LGHorizonVOD,
    LGHorizonVODSource,
    LGHorizonVODType,
    LGHOrizonRelevantEpisode,
)


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestLGHorizonRunningState:
    def test_members(self):
        assert LGHorizonRunningState.UNKNOWN.value == "UNKNOWN"
        assert LGHorizonRunningState.ONLINE_RUNNING.value == "ONLINE_RUNNING"
        assert LGHorizonRunningState.ONLINE_STANDBY.value == "ONLINE_STANDBY"
        assert LGHorizonRunningState.OFFLINE_NETWORK_STANDBY.value == "OFFLINE_NETWORK_STANDBY"
        assert LGHorizonRunningState.OFFLINE.value == "OFFLINE"

    def test_all_members_count(self):
        assert len(LGHorizonRunningState) == 5


class TestLGHorizonMessageType:
    def test_members(self):
        assert LGHorizonMessageType.UNKNOWN.value == 0
        assert LGHorizonMessageType.STATUS.value == 1
        assert LGHorizonMessageType.UI_STATUS.value == 2

    def test_all_members_count(self):
        assert len(LGHorizonMessageType) == 3


class TestLGHorizonRecordingSource:
    def test_members(self):
        assert LGHorizonRecordingSource.SHOW.value == "show"
        assert LGHorizonRecordingSource.SINGLE.value == "single"
        assert LGHorizonRecordingSource.SEASON.value == "season"
        assert LGHorizonRecordingSource.UNKNOWN.value == "unknown"

    def test_all_members_count(self):
        assert len(LGHorizonRecordingSource) == 4


class TestLGHorizonRecordingState:
    def test_members(self):
        assert LGHorizonRecordingState.RECORDED.value == "recorded"
        assert LGHorizonRecordingState.ONGOING.value == "ongoing"
        assert LGHorizonRecordingState.UNKNOWN.value == "unknown"

    def test_all_members_count(self):
        assert len(LGHorizonRecordingState) == 3


class TestLGHorizonRecordingType:
    def test_members(self):
        assert LGHorizonRecordingType.SINGLE.value == "single"
        assert LGHorizonRecordingType.SEASON.value == "season"
        assert LGHorizonRecordingType.SHOW.value == "show"
        assert LGHorizonRecordingType.UNKNOWN.value == "unknown"

    def test_all_members_count(self):
        assert len(LGHorizonRecordingType) == 4


class TestLGHorizonUIStateType:
    def test_members(self):
        assert LGHorizonUIStateType.MAINUI.value == "mainUI"
        assert LGHorizonUIStateType.APPS.value == "apps"
        assert LGHorizonUIStateType.UNKNOWN.value == "unknown"

    def test_all_members_count(self):
        assert len(LGHorizonUIStateType) == 3


class TestLGHorizonMediaType:
    def test_members(self):
        assert LGHorizonMediaType.UNKNOWN.value == "unknown"
        assert LGHorizonMediaType.CHANNEL.value == "channel"
        assert LGHorizonMediaType.APP.value == "app"
        assert LGHorizonMediaType.MOVIE.value == "movie"
        assert LGHorizonMediaType.EPISODE.value == "episode"
        assert LGHorizonMediaType.TVSHOW.value == "tvshow"

    def test_all_members_count(self):
        assert len(LGHorizonMediaType) == 6


class TestLGHorizonSourceType:
    def test_members(self):
        assert LGHorizonSourceType.LINEAR.value == "linear"
        assert LGHorizonSourceType.REVIEWBUFFER.value == "reviewBuffer"
        assert LGHorizonSourceType.NDVR.value == "nDVR"
        assert LGHorizonSourceType.LOCALDVR.value == "localDVR"
        assert LGHorizonSourceType.REPLAY.value == "replay"
        assert LGHorizonSourceType.VOD.value == "VOD"
        assert LGHorizonSourceType.UNKNOWN.value == "unknown"

    def test_all_members_count(self):
        assert len(LGHorizonSourceType) == 7


class TestLGHorizonVODType:
    def test_members(self):
        assert LGHorizonVODType.ASSET.value == "ASSET"
        assert LGHorizonVODType.EPISODE.value == "EPISODE"
        assert LGHorizonVODType.UNKNOWN.value == "UNKNOWN"

    def test_all_members_count(self):
        assert len(LGHorizonVODType) == 3


# ---------------------------------------------------------------------------
# LGHorizonChannel
# ---------------------------------------------------------------------------


class TestLGHorizonChannel:
    def test_id(self, sample_channel_json):
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.id == "channel-1"

    def test_channel_number(self, sample_channel_json):
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.channel_number == "1"

    def test_title(self, sample_channel_json):
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.title == "NPO 1"

    def test_is_radio_false(self, sample_channel_json):
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.is_radio is False

    def test_is_radio_true(self, sample_channel_json):
        sample_channel_json["isRadio"] = True
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.is_radio is True

    def test_logo_image(self, sample_channel_json):
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.logo_image == "https://example.com/logo.png"

    def test_logo_image_missing_returns_empty(self, sample_channel_json):
        del sample_channel_json["logo"]
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.logo_image == ""

    def test_logo_image_missing_focused_returns_empty(self, sample_channel_json):
        sample_channel_json["logo"] = {}
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.logo_image == ""

    def test_stream_image_full(self, sample_channel_json):
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.stream_image == "https://example.com/stream.png"

    def test_stream_image_falls_back_to_small(self, sample_channel_json):
        sample_channel_json["imageStream"] = {"small": "https://example.com/small.png"}
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.stream_image == "https://example.com/small.png"

    def test_stream_image_falls_back_to_logo(self, sample_channel_json):
        sample_channel_json["imageStream"] = {}
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.stream_image == "https://example.com/logo.png"

    def test_stream_image_falls_back_to_empty(self, sample_channel_json):
        sample_channel_json["imageStream"] = {}
        del sample_channel_json["logo"]
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.stream_image == ""

    def test_linear_products(self, sample_channel_json):
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.linear_products == ["product-1", "product-2"]

    def test_linear_products_default_empty(self, sample_channel_json):
        del sample_channel_json["linearProducts"]
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.linear_products == []

    def test_replay_pre_padding(self, sample_channel_json):
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.replay_pre_padding == 10

    def test_replay_post_padding(self, sample_channel_json):
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.replay_post_padding == 5

    def test_replay_padding_defaults(self, sample_channel_json):
        del sample_channel_json["replayPrePadding"]
        del sample_channel_json["replayPostPadding"]
        ch = LGHorizonChannel(sample_channel_json)
        assert ch.replay_pre_padding == 0
        assert ch.replay_post_padding == 0


# ---------------------------------------------------------------------------
# LGHorizonCustomer
# ---------------------------------------------------------------------------


class TestLGHorizonCustomer:
    def test_customer_id(self, sample_customer_json):
        c = LGHorizonCustomer(sample_customer_json)
        assert c.customer_id == "cust-123"

    def test_hashed_customer_id(self, sample_customer_json):
        c = LGHorizonCustomer(sample_customer_json)
        assert c.hashed_customer_id == "hashed-cust-123"

    def test_country_id(self, sample_customer_json):
        c = LGHorizonCustomer(sample_customer_json)
        assert c.country_id == "nl"

    def test_city_id(self, sample_customer_json):
        c = LGHorizonCustomer(sample_customer_json)
        assert c.city_id == 1234

    def test_assigned_devices(self, sample_customer_json):
        c = LGHorizonCustomer(sample_customer_json)
        assert len(c.assigned_devices) == 1
        assert c.assigned_devices[0]["deviceId"] == "device-1"

    def test_profiles_returns_dict_of_profile(self, sample_customer_json):
        c = LGHorizonCustomer(sample_customer_json)
        profiles = c.profiles
        assert isinstance(profiles, dict)
        assert "profile-1" in profiles
        assert "profile-2" in profiles
        assert isinstance(profiles["profile-1"], LGHorizonProfile)

    def test_has_cloud_recording_true(self, sample_customer_json):
        c = LGHorizonCustomer(sample_customer_json)
        result = c.has_cloud_recording
        assert result is True
        assert isinstance(result, bool)

    def test_has_cloud_recording_false_when_zero(self, sample_customer_json):
        sample_customer_json["recordingRetentionPeriod"] = 0
        c = LGHorizonCustomer(sample_customer_json)
        result = c.has_cloud_recording
        assert result is False
        assert isinstance(result, bool)

    def test_has_cloud_recording_false_when_missing(self, sample_customer_json):
        del sample_customer_json["recordingRetentionPeriod"]
        c = LGHorizonCustomer(sample_customer_json)
        result = c.has_cloud_recording
        assert result is False
        assert isinstance(result, bool)

    async def test_get_profile_lang_known(self, sample_customer_json):
        c = LGHorizonCustomer(sample_customer_json)
        lang = c.get_profile_lang("profile-2")
        assert lang == "en"

    async def test_get_profile_lang_default_nl(self, sample_customer_json):
        c = LGHorizonCustomer(sample_customer_json)
        lang = c.get_profile_lang("nonexistent-profile")
        assert lang == "nl"

    def test_profiles_not_shared_between_instances(self, sample_customer_json):
        import copy
        c1 = LGHorizonCustomer(copy.deepcopy(sample_customer_json))
        c2 = LGHorizonCustomer(copy.deepcopy(sample_customer_json))
        # Each instance should have its own _profiles dict
        _ = c1.profiles
        _ = c2.profiles
        assert c1._profiles is not c2._profiles


# ---------------------------------------------------------------------------
# LGHorizonProfile
# ---------------------------------------------------------------------------


class TestLGHorizonProfile:
    def test_id(self):
        payload = {
            "profileId": "p-1",
            "name": "Alice",
            "favoriteChannels": ["ch-1", "ch-2"],
            "options": {"lang": "nl"},
        }
        p = LGHorizonProfile(payload)
        assert p.id == "p-1"

    def test_name(self):
        payload = {
            "profileId": "p-1",
            "name": "Alice",
            "favoriteChannels": [],
            "options": {"lang": "nl"},
        }
        p = LGHorizonProfile(payload)
        assert p.name == "Alice"

    def test_favorite_channels(self):
        payload = {
            "profileId": "p-1",
            "name": "Alice",
            "favoriteChannels": ["ch-1", "ch-2"],
            "options": {"lang": "nl"},
        }
        p = LGHorizonProfile(payload)
        assert p.favorite_channels == ["ch-1", "ch-2"]

    def test_favorite_channels_defaults_empty(self):
        payload = {
            "profileId": "p-1",
            "name": "Alice",
            "options": {"lang": "nl"},
        }
        p = LGHorizonProfile(payload)
        assert p.favorite_channels == []

    def test_options_lang(self):
        payload = {
            "profileId": "p-1",
            "name": "Alice",
            "options": {"lang": "fr"},
        }
        p = LGHorizonProfile(payload)
        assert p.options.lang == "fr"


# ---------------------------------------------------------------------------
# LGHorizonDeviceState
# ---------------------------------------------------------------------------


class TestLGHorizonDeviceState:
    def test_initial_defaults_none(self):
        ds = LGHorizonDeviceState()
        assert ds.channel_id is None
        assert ds.channel_name is None
        assert ds.show_title is None
        assert ds.episode_title is None
        assert ds.season_number is None
        assert ds.episode_number is None
        assert ds.image is None
        assert ds.speed is None
        assert ds.id is None
        assert ds.start_time is None
        assert ds.end_time is None
        assert ds.duration is None
        assert ds.position is None
        assert ds.last_position_update is None

    def test_initial_enum_defaults(self):
        ds = LGHorizonDeviceState()
        assert ds.source_type == LGHorizonSourceType.UNKNOWN
        assert ds.state == LGHorizonRunningState.UNKNOWN
        assert ds.media_type == LGHorizonMediaType.UNKNOWN
        assert ds.ui_state_type == LGHorizonUIStateType.UNKNOWN

    def test_app_name_initialized(self):
        ds = LGHorizonDeviceState()
        # _app_name should be initialized in __init__ (bug we fixed)
        assert ds.app_name is None

    def test_paused_when_speed_zero(self):
        ds = LGHorizonDeviceState()
        ds.speed = 0
        assert ds.paused is True

    def test_not_paused_when_speed_one(self):
        ds = LGHorizonDeviceState()
        ds.speed = 1
        assert ds.paused is False

    def test_not_paused_when_speed_none(self):
        ds = LGHorizonDeviceState()
        ds.speed = None
        assert ds.paused is False

    def test_reset_clears_all_fields(self):
        ds = LGHorizonDeviceState()
        ds.channel_id = "ch-1"
        ds.show_title = "Show"
        ds.episode_title = "Ep"
        ds.season_number = 2
        ds.episode_number = 3
        ds.image = "http://img"
        ds.speed = 1
        ds.channel_name = "NPO"
        ds.id = "some-id"
        ds.start_time = 100
        ds.end_time = 200
        ds.duration = 1800.0
        ds.position = 900.0
        ds.last_position_update = 12345
        ds.source_type = LGHorizonSourceType.LINEAR
        ds.media_type = LGHorizonMediaType.CHANNEL

        ds.reset()

        assert ds.channel_id is None
        assert ds.show_title is None
        assert ds.episode_title is None
        assert ds.season_number is None
        assert ds.episode_number is None
        assert ds.image is None
        assert ds.speed is None
        assert ds.channel_name is None
        assert ds.id is None
        assert ds.start_time is None
        assert ds.end_time is None
        assert ds.duration is None
        assert ds.position is None
        assert ds.last_position_update is None
        assert ds.source_type == LGHorizonSourceType.UNKNOWN
        assert ds.media_type == LGHorizonMediaType.UNKNOWN

    def test_reset_progress_clears_only_progress(self):
        ds = LGHorizonDeviceState()
        ds.channel_id = "ch-1"
        ds.duration = 1800.0
        ds.position = 900.0
        ds.last_position_update = 12345

        ds.reset_progress()

        # Progress fields cleared
        assert ds.duration is None
        assert ds.position is None
        assert ds.last_position_update is None
        # Non-progress fields preserved
        assert ds.channel_id == "ch-1"


# ---------------------------------------------------------------------------
# LGHorizonPlayerState
# ---------------------------------------------------------------------------


class TestLGHorizonPlayerState:
    def test_source_type_linear(self):
        ps = LGHorizonPlayerState({"sourceType": "linear", "speed": 1})
        assert ps.source_type == LGHorizonSourceType.LINEAR

    def test_speed(self):
        ps = LGHorizonPlayerState({"sourceType": "linear", "speed": 2})
        assert ps.speed == 2

    def test_speed_default(self):
        ps = LGHorizonPlayerState({})
        assert ps.speed == 0

    def test_last_speed_change_time(self):
        ps = LGHorizonPlayerState({"lastSpeedChangeTime": 1700000000})
        assert ps.last_speed_change_time == 1700000.0

    def test_relative_position(self):
        ps = LGHorizonPlayerState({"relativePosition": 60000})
        assert ps.relative_position == 60000

    def test_source_linear(self):
        raw = {
            "sourceType": "linear",
            "speed": 1,
            "source": {"channelId": "ch-1", "eventId": "ev-1"},
        }
        ps = LGHorizonPlayerState(raw)
        src = ps.source
        assert isinstance(src, LGHorizonLinearSource)
        assert src.channel_id == "ch-1"
        assert src.event_id == "ev-1"

    def test_source_vod(self):
        raw = {
            "sourceType": "VOD",
            "speed": 1,
            "source": {"titleId": "title-1", "startIntroTime": 5, "endIntroTime": 30},
        }
        ps = LGHorizonPlayerState(raw)
        src = ps.source
        assert isinstance(src, LGHorizonVODSource)
        assert src.title_id == "title-1"

    def test_source_replay(self):
        raw = {
            "sourceType": "replay",
            "speed": 1,
            "source": {"eventId": "ev-99"},
        }
        ps = LGHorizonPlayerState(raw)
        src = ps.source
        assert isinstance(src, LGHorizonReplaySource)
        assert src.event_id == "ev-99"

    def test_source_ndvr(self):
        raw = {
            "sourceType": "nDVR",
            "speed": 1,
            "source": {"recordingId": "rec-5", "channelId": "ch-1"},
        }
        ps = LGHorizonPlayerState(raw)
        src = ps.source
        assert isinstance(src, LGHorizonNDVRSource)
        assert src.recording_id == "rec-5"
        assert src.channel_id == "ch-1"

    def test_source_reviewbuffer(self):
        raw = {
            "sourceType": "reviewBuffer",
            "speed": 1,
            "source": {"channelId": "ch-2", "eventId": "ev-2"},
        }
        ps = LGHorizonPlayerState(raw)
        src = ps.source
        assert isinstance(src, LGHorizonReviewBufferSource)
        assert src.channel_id == "ch-2"

    def test_source_returns_none_when_key_missing(self):
        """Bug fix: source should return None when 'source' key is missing."""
        ps = LGHorizonPlayerState({"sourceType": "linear", "speed": 1})
        assert ps.source is None


# ---------------------------------------------------------------------------
# Source classes
# ---------------------------------------------------------------------------


class TestLGHorizonLinearSource:
    def test_source_type(self):
        src = LGHorizonLinearSource({"channelId": "ch-1", "eventId": "ev-1"})
        assert src.source_type == LGHorizonSourceType.LINEAR

    def test_channel_id(self):
        src = LGHorizonLinearSource({"channelId": "ch-1"})
        assert src.channel_id == "ch-1"

    def test_event_id(self):
        src = LGHorizonLinearSource({"eventId": "ev-1"})
        assert src.event_id == "ev-1"

    def test_defaults(self):
        src = LGHorizonLinearSource({})
        assert src.channel_id == ""
        assert src.event_id == ""


class TestLGHorizonVODSource:
    def test_source_type(self):
        src = LGHorizonVODSource({})
        assert src.source_type == LGHorizonSourceType.VOD

    def test_title_id(self):
        src = LGHorizonVODSource({"titleId": "title-1"})
        assert src.title_id == "title-1"

    def test_start_intro_time(self):
        src = LGHorizonVODSource({"startIntroTime": 10})
        assert src.start_intro_time == 10

    def test_end_intro_time(self):
        src = LGHorizonVODSource({"endIntroTime": 90})
        assert src.end_intro_time == 90

    def test_defaults(self):
        src = LGHorizonVODSource({})
        assert src.title_id == ""
        assert src.start_intro_time == 0
        assert src.end_intro_time == 0


class TestLGHorizonReplaySource:
    def test_source_type(self):
        src = LGHorizonReplaySource({})
        assert src.source_type == LGHorizonSourceType.REPLAY

    def test_event_id(self):
        src = LGHorizonReplaySource({"eventId": "ev-42"})
        assert src.event_id == "ev-42"

    def test_default_event_id(self):
        src = LGHorizonReplaySource({})
        assert src.event_id == ""


class TestLGHorizonNDVRSource:
    def test_source_type(self):
        src = LGHorizonNDVRSource({})
        assert src.source_type == LGHorizonSourceType.NDVR

    def test_recording_id(self):
        src = LGHorizonNDVRSource({"recordingId": "rec-7"})
        assert src.recording_id == "rec-7"

    def test_channel_id(self):
        src = LGHorizonNDVRSource({"channelId": "ch-3"})
        assert src.channel_id == "ch-3"

    def test_defaults(self):
        src = LGHorizonNDVRSource({})
        assert src.recording_id == ""
        assert src.channel_id == ""


class TestLGHorizonReviewBufferSource:
    def test_source_type(self):
        src = LGHorizonReviewBufferSource({})
        assert src.source_type == LGHorizonSourceType.REVIEWBUFFER

    def test_channel_id(self):
        src = LGHorizonReviewBufferSource({"channelId": "ch-rb"})
        assert src.channel_id == "ch-rb"

    def test_event_id(self):
        src = LGHorizonReviewBufferSource({"eventId": "ev-rb"})
        assert src.event_id == "ev-rb"


# ---------------------------------------------------------------------------
# LGHorizonUIState
# ---------------------------------------------------------------------------


class TestLGHorizonUIState:
    def test_ui_status_mainui(self):
        ui = LGHorizonUIState({"uiStatus": "mainUI"})
        assert ui.ui_status == LGHorizonUIStateType.MAINUI

    def test_ui_status_apps(self):
        ui = LGHorizonUIState({"uiStatus": "apps"})
        assert ui.ui_status == LGHorizonUIStateType.APPS

    def test_ui_status_unknown_default(self):
        ui = LGHorizonUIState({})
        assert ui.ui_status == LGHorizonUIStateType.UNKNOWN

    def test_player_state_lazy_init(self):
        raw = {
            "uiStatus": "mainUI",
            "playerState": {
                "sourceType": "linear",
                "speed": 1,
                "source": {"channelId": "ch-1", "eventId": "ev-1"},
            },
        }
        ui = LGHorizonUIState(raw)
        assert ui.player_state is not None
        assert isinstance(ui.player_state, LGHorizonPlayerState)

    def test_player_state_none_when_missing(self):
        ui = LGHorizonUIState({"uiStatus": "mainUI"})
        assert ui.player_state is None

    def test_apps_state_lazy_init(self):
        raw = {
            "uiStatus": "apps",
            "appsState": {"id": "app-1", "appName": "Netflix", "logoPath": "/logo.png"},
        }
        ui = LGHorizonUIState(raw)
        assert ui.apps_state is not None
        assert isinstance(ui.apps_state, LGHorizonAppsState)
        assert ui.apps_state.id == "app-1"
        assert ui.apps_state.app_name == "Netflix"

    def test_apps_state_none_when_missing(self):
        ui = LGHorizonUIState({"uiStatus": "mainUI"})
        assert ui.apps_state is None


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


class TestLGHorizonStatusMessage:
    def test_message_type(self, sample_status_payload):
        msg = LGHorizonStatusMessage(sample_status_payload, "test/topic")
        assert msg.message_type == LGHorizonMessageType.STATUS

    def test_source(self, sample_status_payload):
        msg = LGHorizonStatusMessage(sample_status_payload, "test/topic")
        assert msg.source == "device-1"

    def test_source_default(self):
        msg = LGHorizonStatusMessage({}, "test/topic")
        assert msg.source == "unknown"

    def test_running_state(self, sample_status_payload):
        msg = LGHorizonStatusMessage(sample_status_payload, "test/topic")
        assert msg.running_state == LGHorizonRunningState.ONLINE_RUNNING

    def test_topic(self, sample_status_payload):
        msg = LGHorizonStatusMessage(sample_status_payload, "my/topic")
        assert msg.topic == "my/topic"

    def test_payload(self, sample_status_payload):
        msg = LGHorizonStatusMessage(sample_status_payload, "test/topic")
        assert msg.payload == sample_status_payload


class TestLGHorizonUIStatusMessage:
    def test_message_type(self, sample_ui_status_payload):
        msg = LGHorizonUIStatusMessage(sample_ui_status_payload, "test/topic")
        assert msg.message_type == LGHorizonMessageType.UI_STATUS

    def test_source(self, sample_ui_status_payload):
        msg = LGHorizonUIStatusMessage(sample_ui_status_payload, "test/topic")
        assert msg.source == "device-1"

    def test_message_timestamp(self, sample_ui_status_payload):
        msg = LGHorizonUIStatusMessage(sample_ui_status_payload, "test/topic")
        assert msg.message_timestamp == 1700000.0

    def test_message_timestamp_default(self):
        msg = LGHorizonUIStatusMessage({}, "test/topic")
        assert msg.message_timestamp == 0

    def test_ui_state(self, sample_ui_status_payload):
        msg = LGHorizonUIStatusMessage(sample_ui_status_payload, "test/topic")
        state = msg.ui_state
        assert state is not None
        assert isinstance(state, LGHorizonUIState)
        assert state.ui_status == LGHorizonUIStateType.MAINUI

    def test_ui_state_none_when_missing(self):
        msg = LGHorizonUIStatusMessage({"source": "dev"}, "test/topic")
        assert msg.ui_state is None


class TestLGHorizonUnknownMessage:
    def test_message_type(self):
        msg = LGHorizonUnknownMessage({}, "test/topic")
        assert msg.message_type == LGHorizonMessageType.UNKNOWN

    def test_topic(self):
        msg = LGHorizonUnknownMessage({"data": 1}, "some/topic")
        assert msg.topic == "some/topic"


# ---------------------------------------------------------------------------
# Recordings
# ---------------------------------------------------------------------------


class TestLGHorizonRecordingSingle:
    def test_id(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.id == "rec-1"

    def test_type(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.type == LGHorizonRecordingType.SINGLE

    def test_title(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.title == "Test Recording"

    def test_channel_id(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.channel_id == "channel-1"

    def test_recording_state(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.recording_state == LGHorizonRecordingState.RECORDED

    def test_source(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.source == LGHorizonRecordingSource.SHOW

    def test_episode_title(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.episode_title == "Episode 1"

    def test_episode_id(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.episode_id == "ep-1"

    def test_season_number(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.season_number == 2

    def test_episode_number(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.episode_number == 5

    def test_show_id(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.show_id == "show-1"

    def test_show_title(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.show_title == "Test Show"

    def test_season_id(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.season_id == "season-2"

    def test_duration(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.duration == 3600

    def test_start_time_is_optional_str(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.start_time == "2024-01-15T20:00:00Z"
        assert isinstance(r.start_time, str)

    def test_end_time_is_optional_str(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.end_time == "2024-01-15T21:00:00Z"
        assert isinstance(r.end_time, str)

    def test_start_time_none_when_missing(self):
        r = LGHorizonRecordingSingle({"id": "r", "channelId": "c"})
        assert r.start_time is None

    def test_end_time_none_when_missing(self):
        r = LGHorizonRecordingSingle({"id": "r", "channelId": "c"})
        assert r.end_time is None

    def test_poster_url(self, sample_recording_single_json):
        r = LGHorizonRecordingSingle(sample_recording_single_json)
        assert r.poster_url == "https://example.com/poster.png"

    def test_poster_url_none_when_missing(self):
        r = LGHorizonRecordingSingle({"id": "r", "channelId": "c"})
        assert r.poster_url is None


class TestLGHorizonRecordingSeason:
    def test_id(self, sample_recording_season_json):
        r = LGHorizonRecordingSeason(sample_recording_season_json)
        assert r.id == "rec-season-1"

    def test_no_of_episodes(self, sample_recording_season_json):
        r = LGHorizonRecordingSeason(sample_recording_season_json)
        assert r.no_of_episodes == 10

    def test_season_title(self, sample_recording_season_json):
        r = LGHorizonRecordingSeason(sample_recording_season_json)
        assert r.season_title == "Season 1"

    def test_show_id(self, sample_recording_season_json):
        r = LGHorizonRecordingSeason(sample_recording_season_json)
        assert r.show_id == "show-1"

    def test_most_relevant_episode(self, sample_recording_season_json):
        r = LGHorizonRecordingSeason(sample_recording_season_json)
        ep = r.most_relevant_episode
        assert ep is not None
        assert isinstance(ep, LGHOrizonRelevantEpisode)
        assert ep.season_number == 1
        assert ep.episode_number == 3
        assert ep.recording_state == LGHorizonRecordingState.RECORDED

    def test_most_relevant_episode_none_when_missing(self):
        """Bug fix: most_relevant_episode should be None when key is absent."""
        payload = {
            "id": "rec-s",
            "channelId": "ch-1",
            "noOfEpisodes": 5,
            "seasonTitle": "Season 2",
            "showId": "show-2",
        }
        r = LGHorizonRecordingSeason(payload)
        assert r.most_relevant_episode is None


class TestLGHorizonRecordingShow:
    def test_id(self, sample_recording_show_json):
        r = LGHorizonRecordingShow(sample_recording_show_json)
        assert r.id == "rec-show-1"

    def test_no_of_episodes(self, sample_recording_show_json):
        r = LGHorizonRecordingShow(sample_recording_show_json)
        assert r.no_of_episodes == 25

    def test_most_relevant_episode(self, sample_recording_show_json):
        r = LGHorizonRecordingShow(sample_recording_show_json)
        ep = r.most_relevant_episode
        assert ep is not None
        assert ep.season_number == 2
        assert ep.episode_number == 1

    def test_most_relevant_episode_none_when_missing(self):
        """Bug fix: most_relevant_episode should be None when key is absent."""
        payload = {"id": "rec-sh", "channelId": "ch-1", "noOfEpisodes": 3}
        r = LGHorizonRecordingShow(payload)
        assert r.most_relevant_episode is None


class TestLGHorizonRecordingList:
    def test_total(self, sample_recording_single_json, sample_recording_season_json):
        recordings = [
            LGHorizonRecordingSingle(sample_recording_single_json),
            LGHorizonRecordingSeason(sample_recording_season_json),
        ]
        lst = LGHorizonRecordingList(recordings)
        assert lst.total == 2

    def test_recordings(self, sample_recording_single_json):
        recordings = [LGHorizonRecordingSingle(sample_recording_single_json)]
        lst = LGHorizonRecordingList(recordings)
        assert len(lst.recordings) == 1
        assert lst.recordings[0].id == "rec-1"

    def test_empty_list(self):
        lst = LGHorizonRecordingList([])
        assert lst.total == 0
        assert lst.recordings == []


class TestLGHorizonShowRecordingList:
    def test_show_title(self, sample_recording_single_json):
        lst = LGHorizonShowRecordingList(
            "My Show", "https://example.com/show.png",
            [LGHorizonRecordingSingle(sample_recording_single_json)]
        )
        assert lst.show_title == "My Show"

    def test_show_image(self, sample_recording_single_json):
        lst = LGHorizonShowRecordingList(
            "My Show", "https://example.com/show.png",
            [LGHorizonRecordingSingle(sample_recording_single_json)]
        )
        assert lst.show_image == "https://example.com/show.png"

    def test_show_image_none(self):
        lst = LGHorizonShowRecordingList("My Show", None, [])
        assert lst.show_image is None

    def test_total(self, sample_recording_single_json):
        lst = LGHorizonShowRecordingList(
            "My Show", None,
            [LGHorizonRecordingSingle(sample_recording_single_json)]
        )
        assert lst.total == 1


class TestLGHorizonRecordingQuota:
    def test_quota(self):
        q = LGHorizonRecordingQuota({"quota": 500, "occupied": 250})
        assert q.quota == 500

    def test_occupied(self):
        q = LGHorizonRecordingQuota({"quota": 500, "occupied": 250})
        assert q.occupied == 250

    def test_percentage_used(self):
        q = LGHorizonRecordingQuota({"quota": 500, "occupied": 250})
        assert q.percentage_used == 50.0

    def test_percentage_used_zero_quota(self):
        q = LGHorizonRecordingQuota({"quota": 0, "occupied": 0})
        assert q.percentage_used == 0.0

    def test_percentage_used_full(self):
        q = LGHorizonRecordingQuota({"quota": 100, "occupied": 100})
        assert q.percentage_used == 100.0

    def test_defaults(self):
        q = LGHorizonRecordingQuota({})
        assert q.quota == 0
        assert q.occupied == 0
        assert q.percentage_used == 0.0


class TestLGHOrizonRelevantEpisode:
    def test_recording_state(self):
        ep = LGHOrizonRelevantEpisode({"recordingState": "recorded", "seasonNumber": 1, "episodeNumber": 2})
        assert ep.recording_state == LGHorizonRecordingState.RECORDED

    def test_recording_state_default(self):
        ep = LGHOrizonRelevantEpisode({})
        assert ep.recording_state == LGHorizonRecordingState.UNKNOWN

    def test_season_number(self):
        ep = LGHOrizonRelevantEpisode({"seasonNumber": 3})
        assert ep.season_number == 3

    def test_episode_number(self):
        ep = LGHOrizonRelevantEpisode({"episodeNumber": 7})
        assert ep.episode_number == 7

    def test_season_episode_none_when_missing(self):
        ep = LGHOrizonRelevantEpisode({})
        assert ep.season_number is None
        assert ep.episode_number is None


# ---------------------------------------------------------------------------
# LGHorizonReplayEvent
# ---------------------------------------------------------------------------


class TestLGHorizonReplayEvent:
    def test_event_id(self, sample_replay_event_json):
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.event_id == "event-1"

    def test_channel_id(self, sample_replay_event_json):
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.channel_id == "channel-1"

    def test_title(self, sample_replay_event_json):
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.title == "Test Show"

    def test_episode_name(self, sample_replay_event_json):
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.episode_name == "Pilot"

    def test_season_number(self, sample_replay_event_json):
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.season_number == 1

    def test_episode_number(self, sample_replay_event_json):
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.episode_number == 1

    def test_start_time(self, sample_replay_event_json):
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.start_time == 1700000000.0

    def test_end_time(self, sample_replay_event_json):
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.end_time == 1700003600.0

    def test_full_episode_title_with_name(self, sample_replay_event_json):
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.full_episode_title == "S01E01: Pilot"

    def test_full_episode_title_without_name(self, sample_replay_event_json):
        del sample_replay_event_json["episodeName"]
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.full_episode_title == "S01E01"

    def test_full_episode_title_none_when_no_season_or_episode(self):
        ev = LGHorizonReplayEvent({
            "eventId": "ev-1",
            "channelId": "ch-1",
            "title": "Movie",
        })
        assert ev.full_episode_title is None

    def test_episode_name_none_when_missing(self):
        ev = LGHorizonReplayEvent({"eventId": "e", "channelId": "c", "title": "T"})
        assert ev.episode_name is None

    def test_start_end_time_none_when_missing(self):
        ev = LGHorizonReplayEvent({"eventId": "e", "channelId": "c", "title": "T"})
        assert ev.start_time is None
        assert ev.end_time is None


# ---------------------------------------------------------------------------
# LGHorizonVOD
# ---------------------------------------------------------------------------


class TestLGHorizonVOD:
    def test_vod_type(self, sample_vod_json):
        v = LGHorizonVOD(sample_vod_json)
        assert v.vod_type == LGHorizonVODType.EPISODE

    def test_id(self, sample_vod_json):
        v = LGHorizonVOD(sample_vod_json)
        assert v.id == "vod-1"

    def test_title(self, sample_vod_json):
        v = LGHorizonVOD(sample_vod_json)
        assert v.title == "Episode Title"

    def test_series_title(self, sample_vod_json):
        v = LGHorizonVOD(sample_vod_json)
        assert v.series_title == "Series Title"

    def test_series_title_none_when_missing(self):
        v = LGHorizonVOD({"id": "v", "title": "T", "type": "ASSET", "duration": 90.0})
        assert v.series_title is None

    def test_duration(self, sample_vod_json):
        v = LGHorizonVOD(sample_vod_json)
        assert v.duration == 2700.0

    def test_season(self, sample_vod_json):
        v = LGHorizonVOD(sample_vod_json)
        assert v.season == 3

    def test_episode(self, sample_vod_json):
        v = LGHorizonVOD(sample_vod_json)
        assert v.episode == 7

    def test_season_none_when_missing(self):
        v = LGHorizonVOD({"id": "v", "title": "T", "type": "ASSET", "duration": 90.0})
        assert v.season is None

    def test_episode_none_when_missing(self):
        v = LGHorizonVOD({"id": "v", "title": "T", "type": "ASSET", "duration": 90.0})
        assert v.episode is None

    def test_vod_type_unknown(self):
        v = LGHorizonVOD({"id": "v", "title": "T", "duration": 60.0})
        assert v.vod_type == LGHorizonVODType.UNKNOWN


# ---------------------------------------------------------------------------
# LGHorizonServicesConfig
# ---------------------------------------------------------------------------


class TestLGHorizonServicesConfig:
    async def test_get_service_url(self, sample_service_config):
        url = sample_service_config.get_service_url("linearService")
        assert url == "https://linear.example.com"

    async def test_get_service_url_raises_for_unknown(self, sample_service_config):
        with pytest.raises(ValueError):
            sample_service_config.get_service_url("nonExistentService")

    async def test_get_all_services(self, sample_service_config):
        services = sample_service_config.get_all_services()
        assert isinstance(services, dict)
        assert "linearService" in services
        assert "recordingService" in services
        assert services["authorizationService"] == "https://auth.example.com"

    def test_repr_includes_service_count(self, sample_service_config):
        r = repr(sample_service_config)
        assert "8" in r  # 8 services defined in fixture
        assert "LGHorizonConfig" in r


# ---------------------------------------------------------------------------
# LGHorizonEntitlements
# ---------------------------------------------------------------------------


class TestLGHorizonEntitlements:
    def test_entitlements(self):
        data = {
            "entitlements": [
                {"id": "ent-1", "name": "Basic"},
                {"id": "ent-2", "name": "Premium"},
            ]
        }
        e = LGHorizonEntitlements(data)
        assert len(e.entitlements) == 2

    def test_entitlement_ids(self):
        data = {
            "entitlements": [
                {"id": "ent-1", "name": "Basic"},
                {"id": "ent-2", "name": "Premium"},
            ]
        }
        e = LGHorizonEntitlements(data)
        assert e.entitlement_ids == ["ent-1", "ent-2"]

    def test_entitlements_empty(self):
        e = LGHorizonEntitlements({})
        assert e.entitlements == []
        assert e.entitlement_ids == []

    def test_entitlement_ids_skips_missing_id(self):
        data = {
            "entitlements": [
                {"id": "ent-1"},
                {"name": "No ID"},
            ]
        }
        e = LGHorizonEntitlements(data)
        assert e.entitlement_ids == ["ent-1"]


# ---------------------------------------------------------------------------
# LGHorizonEpgEvent
# ---------------------------------------------------------------------------

_EPG_EVENT_JSON = {
    "id": "crid:test",
    "title": "Test Show",
    "startTime": 1000,
    "endTime": 2000,
    "minimumAge": 12,
    "isPlaceHolder": True,
    "mergedId": "123|nl",
    "audioLanguages": [{"lang": "nl"}, {"lang": "en"}],
}


class TestLGHorizonEpgEvent:
    def test_event_id(self):
        ev = LGHorizonEpgEvent(_EPG_EVENT_JSON, "NL_001")
        assert ev.event_id == "crid:test"

    def test_channel_id(self):
        ev = LGHorizonEpgEvent(_EPG_EVENT_JSON, "NL_001")
        assert ev.channel_id == "NL_001"

    def test_title(self):
        ev = LGHorizonEpgEvent(_EPG_EVENT_JSON, "NL_001")
        assert ev.title == "Test Show"

    def test_start_time(self):
        ev = LGHorizonEpgEvent(_EPG_EVENT_JSON, "NL_001")
        assert ev.start_time == 1000

    def test_end_time(self):
        ev = LGHorizonEpgEvent(_EPG_EVENT_JSON, "NL_001")
        assert ev.end_time == 2000

    def test_minimum_age(self):
        ev = LGHorizonEpgEvent(_EPG_EVENT_JSON, "NL_001")
        assert ev.minimum_age == 12

    def test_is_placeholder(self):
        ev = LGHorizonEpgEvent(_EPG_EVENT_JSON, "NL_001")
        assert ev.is_placeholder is True

    def test_merged_id(self):
        ev = LGHorizonEpgEvent(_EPG_EVENT_JSON, "NL_001")
        assert ev.merged_id == "123|nl"

    def test_audio_languages(self):
        ev = LGHorizonEpgEvent(_EPG_EVENT_JSON, "NL_001")
        assert ev.audio_languages == ["nl", "en"]

    def test_defaults_with_empty_dict(self):
        ev = LGHorizonEpgEvent({}, "CH_X")
        assert ev.event_id == ""
        assert ev.channel_id == "CH_X"
        assert ev.title == ""
        assert ev.start_time is None
        assert ev.end_time is None
        assert ev.minimum_age == 0
        assert ev.is_placeholder is False
        assert ev.merged_id is None
        assert ev.audio_languages == []


# ---------------------------------------------------------------------------
# LGHorizonEpgEntry
# ---------------------------------------------------------------------------


class TestLGHorizonEpgEntry:
    def _make_entry(self):
        return LGHorizonEpgEntry({
            "channelId": "NL_001",
            "events": [
                {"id": "e1", "title": "Show1"},
                {"id": "e2", "title": "Show2"},
            ],
        })

    def test_channel_id(self):
        entry = self._make_entry()
        assert entry.channel_id == "NL_001"

    def test_events_count(self):
        entry = self._make_entry()
        assert len(entry.events) == 2

    def test_events_are_epg_event_instances(self):
        entry = self._make_entry()
        for ev in entry.events:
            assert isinstance(ev, LGHorizonEpgEvent)

    def test_events_inherit_channel_id(self):
        entry = self._make_entry()
        for ev in entry.events:
            assert ev.channel_id == "NL_001"

    def test_empty_events(self):
        entry = LGHorizonEpgEntry({"channelId": "NL_002", "events": []})
        assert entry.events == []


# ---------------------------------------------------------------------------
# LGHorizonEpg
# ---------------------------------------------------------------------------


class TestLGHorizonEpg:
    def _make_epg(self):
        entry1 = LGHorizonEpgEntry({
            "channelId": "NL_001",
            "events": [{"id": "e1", "title": "Show1"}],
        })
        entry2 = LGHorizonEpgEntry({
            "channelId": "NL_002",
            "events": [{"id": "e2", "title": "Show2"}, {"id": "e3", "title": "Show3"}],
        })
        return LGHorizonEpg([entry1, entry2])

    def test_entries_property(self):
        epg = self._make_epg()
        assert len(epg.entries) == 2
        for entry in epg.entries:
            assert isinstance(entry, LGHorizonEpgEntry)

    def test_get_channel_events_known_channel(self):
        epg = self._make_epg()
        events = epg.get_channel_events("NL_002")
        assert len(events) == 2
        assert events[0].event_id == "e2"
        assert events[1].event_id == "e3"

    def test_get_channel_events_unknown_channel(self):
        epg = self._make_epg()
        events = epg.get_channel_events("UNKNOWN_CH")
        assert events == []


# ---------------------------------------------------------------------------
# LGHorizonEventDetail
# ---------------------------------------------------------------------------

_EVENT_DETAIL_JSON = {
    "eventId": "e1",
    "channelId": "CH1",
    "title": "Movie Title",
    "episodeName": "Ep1",
    "shortDescription": "Short",
    "longDescription": "Long desc",
    "genres": ["Drama", "Action"],
    "seasonNumber": 2,
    "episodeNumber": 5,
    "startTime": 1000,
    "endTime": 2000,
    "actors": ["Actor1"],
    "directors": ["Dir1"],
    "producers": ["Prod1"],
    "countryOfOrigin": "NL",
    "productionDate": "2024",
    "minimumAge": "12",
    "imageVersion": "abc",
    "seriesId": "s1",
    "parentSeriesId": "ps1",
    "audioLanguages": [{"lang": "nl"}],
    "captionLanguages": [{"lang": "en"}],
}


class TestLGHorizonEventDetail:
    def test_event_id(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.event_id == "e1"

    def test_channel_id(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.channel_id == "CH1"

    def test_title(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.title == "Movie Title"

    def test_episode_name(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.episode_name == "Ep1"

    def test_short_description(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.short_description == "Short"

    def test_long_description(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.long_description == "Long desc"

    def test_description_returns_long_when_both_present(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.description == "Long desc"

    def test_description_returns_short_when_long_is_none(self):
        json_data = {**_EVENT_DETAIL_JSON, "longDescription": None}
        d = LGHorizonEventDetail(json_data)
        assert d.description == "Short"

    def test_genres(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.genres == ["Drama", "Action"]

    def test_season_number(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.season_number == 2

    def test_episode_number(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.episode_number == 5

    def test_start_time(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.start_time == 1000

    def test_end_time(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.end_time == 2000

    def test_actors(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.actors == ["Actor1"]

    def test_directors(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.directors == ["Dir1"]

    def test_producers(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.producers == ["Prod1"]

    def test_country_of_origin(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.country_of_origin == "NL"

    def test_production_date(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.production_date == "2024"

    def test_minimum_age(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.minimum_age == "12"

    def test_image_version(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.image_version == "abc"

    def test_series_id(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.series_id == "s1"

    def test_parent_series_id(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.parent_series_id == "ps1"

    def test_audio_languages(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.audio_languages == ["nl"]

    def test_caption_languages(self):
        d = LGHorizonEventDetail(_EVENT_DETAIL_JSON)
        assert d.caption_languages == ["en"]

    def test_defaults_with_empty_dict(self):
        d = LGHorizonEventDetail({})
        assert d.event_id == ""
        assert d.channel_id == ""
        assert d.title == ""
        assert d.episode_name is None
        assert d.short_description is None
        assert d.long_description is None
        assert d.description is None
        assert d.genres == []
        assert d.season_number is None
        assert d.episode_number is None
        assert d.start_time is None
        assert d.end_time is None
        assert d.actors == []
        assert d.directors == []
        assert d.producers == []
        assert d.country_of_origin is None
        assert d.production_date is None
        assert d.minimum_age is None
        assert d.image_version is None
        assert d.series_id is None
        assert d.parent_series_id is None
        assert d.audio_languages == []
        assert d.caption_languages == []


# ---------------------------------------------------------------------------
# LGHorizonReplayChannel
# ---------------------------------------------------------------------------


class TestLGHorizonReplayChannel:
    def test_id(self):
        ch = LGHorizonReplayChannel({"id": "NL_001", "name": "NPO 1", "logo": "http://logo.png"})
        assert ch.id == "NL_001"

    def test_name(self):
        ch = LGHorizonReplayChannel({"id": "NL_001", "name": "NPO 1", "logo": "http://logo.png"})
        assert ch.name == "NPO 1"

    def test_logo(self):
        ch = LGHorizonReplayChannel({"id": "NL_001", "name": "NPO 1", "logo": "http://logo.png"})
        assert ch.logo == "http://logo.png"

    def test_defaults(self):
        ch = LGHorizonReplayChannel({})
        assert ch.id == ""
        assert ch.name == ""
        assert ch.logo == ""


# ---------------------------------------------------------------------------
# LGHorizonManagedRecording
# ---------------------------------------------------------------------------

_MANAGED_RECORDING_JSON = {
    "id": "r1",
    "title": "Show",
    "showName": "ShowName",
    "seasonName": "S1",
    "itemType": "single",
    "recordingState": "recorded",
    "recordingType": "nDVR",
    "channelId": "CH1",
    "seasonNumber": 1,
    "episodeNumber": 3,
    "seasonId": "sid",
    "showId": "shid",
    "source": "show",
    "diskSpace": 0.5,
    "recDuration": 3600,
    "displayStartTime": "2026-01-01T00:00:00Z",
    "displayEndTime": "2026-01-01T01:00:00Z",
    "recStartTime": "2025-12-31T23:55:00Z",
    "recEndTime": "2026-01-01T01:10:00Z",
    "deleteTime": "2027-01-01T00:00:00Z",
    "bookingTime": "2025-12-01T00:00:00Z",
    "retentionPeriod": 365,
    "prePaddingOffset": 300,
    "postPaddingOffset": 600,
    "isPremiere": True,
    "isAdult": False,
    "minimumAge": "12",
    "autoDeletionProtected": True,
}


class TestLGHorizonManagedRecording:
    def test_id(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.id == "r1"

    def test_title(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.title == "Show"

    def test_show_name(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.show_name == "ShowName"

    def test_season_name(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.season_name == "S1"

    def test_item_type(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.item_type == "single"

    def test_recording_state(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.recording_state == "recorded"

    def test_recording_type(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.recording_type == "nDVR"

    def test_channel_id(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.channel_id == "CH1"

    def test_season_number(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.season_number == 1

    def test_episode_number(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.episode_number == 3

    def test_season_id(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.season_id == "sid"

    def test_show_id(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.show_id == "shid"

    def test_source(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.source == "show"

    def test_disk_space(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.disk_space == 0.5

    def test_duration(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.duration == 3600

    def test_start_time(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.start_time == "2026-01-01T00:00:00Z"

    def test_end_time(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.end_time == "2026-01-01T01:00:00Z"

    def test_rec_start_time(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.rec_start_time == "2025-12-31T23:55:00Z"

    def test_rec_end_time(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.rec_end_time == "2026-01-01T01:10:00Z"

    def test_delete_time(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.delete_time == "2027-01-01T00:00:00Z"

    def test_booking_time(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.booking_time == "2025-12-01T00:00:00Z"

    def test_retention_period(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.retention_period == 365

    def test_pre_padding_offset(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.pre_padding_offset == 300

    def test_post_padding_offset(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.post_padding_offset == 600

    def test_is_premiere(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.is_premiere is True

    def test_is_adult(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.is_adult is False

    def test_minimum_age(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.minimum_age == "12"

    def test_auto_deletion_protected(self):
        r = LGHorizonManagedRecording(_MANAGED_RECORDING_JSON)
        assert r.auto_deletion_protected is True

    def test_defaults_with_empty_dict(self):
        r = LGHorizonManagedRecording({})
        assert r.id == ""
        assert r.title == ""
        assert r.show_name is None
        assert r.season_name is None
        assert r.item_type == ""
        assert r.recording_state == ""
        assert r.recording_type == ""
        assert r.channel_id is None
        assert r.season_number is None
        assert r.episode_number is None
        assert r.season_id is None
        assert r.show_id is None
        assert r.source is None
        assert r.disk_space == 0.0
        assert r.duration is None
        assert r.start_time is None
        assert r.end_time is None
        assert r.rec_start_time is None
        assert r.rec_end_time is None
        assert r.delete_time is None
        assert r.booking_time is None
        assert r.retention_period is None
        assert r.pre_padding_offset is None
        assert r.post_padding_offset is None
        assert r.is_premiere is False
        assert r.is_adult is False
        assert r.minimum_age is None
        assert r.auto_deletion_protected is False


# ---------------------------------------------------------------------------
# LGHorizonManagedRecordingList
# ---------------------------------------------------------------------------


class TestLGHorizonManagedRecordingList:
    def _make_list(self):
        return LGHorizonManagedRecordingList({
            "total": 100,
            "limit": 50,
            "offset": 0,
            "data": [
                {"diskSpace": 0.5, "id": "r1"},
                {"diskSpace": 1.0, "id": "r2"},
            ],
        })

    def test_total(self):
        lst = self._make_list()
        assert lst.total == 100

    def test_limit(self):
        lst = self._make_list()
        assert lst.limit == 50

    def test_offset(self):
        lst = self._make_list()
        assert lst.offset == 0

    def test_recordings_count(self):
        lst = self._make_list()
        assert len(lst.recordings) == 2

    def test_recordings_are_managed_recording_instances(self):
        lst = self._make_list()
        for r in lst.recordings:
            assert isinstance(r, LGHorizonManagedRecording)

    def test_total_disk_space(self):
        lst = self._make_list()
        assert lst.total_disk_space == pytest.approx(1.5)

    def test_empty_data(self):
        lst = LGHorizonManagedRecordingList({"total": 0, "limit": 50, "offset": 0, "data": []})
        assert lst.recordings == []
        assert lst.total_disk_space == 0.0

    def test_defaults_with_empty_dict(self):
        lst = LGHorizonManagedRecordingList({})
        assert lst.total == 0
        assert lst.limit == 0
        assert lst.offset == 0
        assert lst.recordings == []
        assert lst.total_disk_space == 0.0


# ---------------------------------------------------------------------------
# Helpers for TestAuthRequest
# ---------------------------------------------------------------------------

from aiohttp import ClientResponseError, RequestInfo
from yarl import URL

from lghorizon.lghorizon_models import LGHorizonAuth
from lghorizon.exceptions import LGHorizonApiConnectionError


def make_response_error(status: int) -> ClientResponseError:
    request_info = RequestInfo(
        url=URL("http://test"),
        method="GET",
        headers={},  # type: ignore[arg-type]
        real_url=URL("http://test"),
    )
    return ClientResponseError(request_info, (), status=status, message="error")


def make_auth() -> LGHorizonAuth:
    """Return an LGHorizonAuth with a mocked websession."""
    mock_session = MagicMock()
    mock_session.request = AsyncMock()
    auth = LGHorizonAuth(
        websession=mock_session,
        country_code="nl",
        username="user",
        password="pass",
    )
    # Prevent proactive token refresh from interfering
    auth.is_token_expiring = MagicMock(return_value=False)
    # Mock fetch_access_token so it doesn't hit the network
    auth.fetch_access_token = AsyncMock()
    return auth


def make_ok_response(data=None):
    resp = AsyncMock()
    resp.raise_for_status = MagicMock()  # no-op — success
    resp.json = AsyncMock(return_value=data or {"key": "value"})
    return resp


def make_error_response(status: int):
    resp = AsyncMock()
    resp.raise_for_status = MagicMock(side_effect=make_response_error(status))
    resp.json = AsyncMock(return_value={})
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAuthRequest:
    """Tests for the 401 retry logic in LGHorizonAuth.request()."""

    async def test_request_success(self):
        """Normal successful request returns JSON response."""
        auth = make_auth()
        auth.websession.request = AsyncMock(return_value=make_ok_response({"result": "ok"}))

        result = await auth.request("http://host", "/path")

        assert result == {"result": "ok"}
        auth.websession.request.assert_called_once()
        auth.fetch_access_token.assert_not_called()

    async def test_request_401_retries_and_succeeds(self):
        """First request returns 401; after token refresh the retry succeeds."""
        auth = make_auth()
        auth.websession.request = AsyncMock(
            side_effect=[make_error_response(401), make_ok_response({"retry": "ok"})]
        )

        result = await auth.request("http://host", "/path")

        assert result == {"retry": "ok"}
        auth.fetch_access_token.assert_called_once()
        assert auth.websession.request.call_count == 2

    async def test_request_401_retry_also_fails(self):
        """First request returns 401; retry also fails → LGHorizonApiConnectionError.

        The backoff decorator may re-invoke request() multiple times, but each
        invocation should call fetch_access_token exactly once (for the 401),
        so the total fetch_access_token call count equals the number of
        top-level backoff attempts.
        """
        auth = make_auth()
        # Every call to websession.request returns 401
        auth.websession.request = AsyncMock(return_value=make_error_response(401))

        with pytest.raises(LGHorizonApiConnectionError):
            await auth.request("http://host", "/path")

        # fetch_access_token must have been called at least once (once per backoff attempt)
        auth.fetch_access_token.assert_called()

    async def test_request_non_401_error_no_retry(self):
        """Non-401 error is raised immediately without calling fetch_access_token.

        Note: the @backoff decorator may retry up to max_tries=3 times on
        LGHorizonApiConnectionError, but fetch_access_token must never be called
        because the error is not a 401.
        """
        auth = make_auth()
        # Always return 403 — no matter how many times backoff retries
        auth.websession.request = AsyncMock(return_value=make_error_response(403))

        with pytest.raises(LGHorizonApiConnectionError):
            await auth.request("http://host", "/path")

        # fetch_access_token must never be called for non-401 errors
        auth.fetch_access_token.assert_not_called()
        # backoff may call request up to max_tries (3) times, but never 0
        assert auth.websession.request.call_count >= 1

    async def test_request_401_refreshes_token_before_retry(self):
        """fetch_access_token is called BEFORE the retry request."""
        call_order: list[str] = []

        auth = make_auth()

        async def fake_fetch():
            call_order.append("fetch_access_token")

        auth.fetch_access_token = fake_fetch  # type: ignore[assignment]

        async def fake_request(*args, **kwargs):
            call_order.append(f"request_{len(call_order)}")
            if call_order.count("request_0") == 1 and call_order[0] == "request_0":
                return make_error_response(401)
            return make_ok_response()

        # Simpler: track via side_effect list
        responses = [make_error_response(401), make_ok_response()]
        request_calls: list[str] = []

        async def tracking_request(*args, **kwargs):
            resp = responses.pop(0)
            request_calls.append("request")
            call_order.append("request")
            return resp

        auth.websession.request = tracking_request  # type: ignore[assignment]

        result = await auth.request("http://host", "/path")

        assert result == {"key": "value"}
        # Order must be: first request → fetch_access_token → retry request
        assert call_order[0] == "request"
        fetch_idx = call_order.index("fetch_access_token")
        last_request_idx = len(call_order) - 1 - call_order[::-1].index("request")
        assert fetch_idx < last_request_idx, (
            f"fetch_access_token (idx {fetch_idx}) should come before retry request (idx {last_request_idx})"
        )


class TestNdvrTimestampParsing:
    """Tests for LGHorizonDeviceStateProcessor._parse_timestamp helper."""

    def _make_processor(self):
        from lghorizon.lghorizon_device_state_processor import LGHorizonDeviceStateProcessor
        return LGHorizonDeviceStateProcessor(None, {}, None, None)

    def test_numeric_epoch_seconds(self):
        proc = self._make_processor()
        assert proc._parse_timestamp(1714060800) == 1714060800

    def test_numeric_float(self):
        proc = self._make_processor()
        assert proc._parse_timestamp(1714060800.9) == 1714060800

    def test_iso8601_string(self):
        proc = self._make_processor()
        result = proc._parse_timestamp("2024-04-25T20:00:00Z")
        assert result == 1714075200

    def test_none_returns_none(self):
        proc = self._make_processor()
        assert proc._parse_timestamp(None) is None

    def test_invalid_string_returns_none(self):
        proc = self._make_processor()
        assert proc._parse_timestamp("not-a-date") is None


# ---------------------------------------------------------------------------
# TestAdBreaks
# ---------------------------------------------------------------------------

# Fixture ad manifest from captured MQTT data
_AD_MANIFEST_RAW = [
    {"dStart": 0, "dEnd": 15000, "adType": "IP_OTHER", "adCounter": True, "isSkippable": False},
    {"dStart": 527760, "dEnd": 1012640, "adType": "IP_OTHER", "adCounter": True, "isSkippable": False},
    {"dStart": 1815360, "dEnd": 1846360, "adType": "IP_OTHER", "adCounter": True, "isSkippable": False},
]


class TestAdBreaks:
    # ------------------------------------------------------------------
    # LGHorizonAdBreak dataclass properties
    # ------------------------------------------------------------------

    def test_duration_ms(self):
        ab = LGHorizonAdBreak(start_ms=527760, end_ms=1012640, ad_type="IP_OTHER", is_skippable=False, has_counter=True)
        assert ab.duration_ms == 1012640 - 527760

    def test_start_s(self):
        ab = LGHorizonAdBreak(start_ms=527760, end_ms=1012640, ad_type="IP_OTHER", is_skippable=False, has_counter=True)
        assert ab.start_s == 527760 / 1000

    def test_end_s(self):
        ab = LGHorizonAdBreak(start_ms=527760, end_ms=1012640, ad_type="IP_OTHER", is_skippable=False, has_counter=True)
        assert ab.end_s == 1012640 / 1000

    def test_duration_ms_first_break(self):
        ab = LGHorizonAdBreak(start_ms=0, end_ms=15000, ad_type="IP_OTHER", is_skippable=False, has_counter=True)
        assert ab.duration_ms == 15000

    def test_start_s_zero(self):
        ab = LGHorizonAdBreak(start_ms=0, end_ms=15000, ad_type="IP_OTHER", is_skippable=False, has_counter=True)
        assert ab.start_s == 0.0

    def test_end_s_first_break(self):
        ab = LGHorizonAdBreak(start_ms=0, end_ms=15000, ad_type="IP_OTHER", is_skippable=False, has_counter=True)
        assert ab.end_s == 15.0

    # ------------------------------------------------------------------
    # LGHorizonNDVRSource.ad_manifest property
    # ------------------------------------------------------------------

    def test_ad_manifest_parses_breaks(self):
        src = LGHorizonNDVRSource({"recordingId": "rec-1", "adManifest": _AD_MANIFEST_RAW})
        breaks = src.ad_manifest
        assert len(breaks) == 3
        for ab in breaks:
            assert isinstance(ab, LGHorizonAdBreak)

    def test_ad_manifest_correct_values(self):
        src = LGHorizonNDVRSource({"adManifest": _AD_MANIFEST_RAW})
        breaks = src.ad_manifest
        assert breaks[0].start_ms == 0
        assert breaks[0].end_ms == 15000
        assert breaks[0].ad_type == "IP_OTHER"
        assert breaks[0].is_skippable is False
        assert breaks[0].has_counter is True
        assert breaks[1].start_ms == 527760
        assert breaks[1].end_ms == 1012640
        assert breaks[2].start_ms == 1815360
        assert breaks[2].end_ms == 1846360

    def test_ad_manifest_no_key_returns_empty_list(self):
        src = LGHorizonNDVRSource({"recordingId": "rec-1"})
        assert src.ad_manifest == []

    def test_ad_manifest_empty_array_returns_empty_list(self):
        src = LGHorizonNDVRSource({"recordingId": "rec-1", "adManifest": []})
        assert src.ad_manifest == []

    # ------------------------------------------------------------------
    # LGHorizonDeviceState.is_in_ad_break
    # ------------------------------------------------------------------

    def _make_state_with_breaks(self) -> LGHorizonDeviceState:
        ds = LGHorizonDeviceState()
        ds.ad_breaks = [
            LGHorizonAdBreak(start_ms=0, end_ms=15000, ad_type="IP_OTHER", is_skippable=False, has_counter=True),
            LGHorizonAdBreak(start_ms=527760, end_ms=1012640, ad_type="IP_OTHER", is_skippable=False, has_counter=True),
            LGHorizonAdBreak(start_ms=1815360, end_ms=1846360, ad_type="IP_OTHER", is_skippable=False, has_counter=True),
        ]
        return ds

    def test_is_in_ad_break_no_breaks(self):
        ds = LGHorizonDeviceState()
        ds.position = 10.0
        assert ds.is_in_ad_break is False

    def test_is_in_ad_break_position_none(self):
        ds = self._make_state_with_breaks()
        ds.position = None
        assert ds.is_in_ad_break is False

    def test_is_in_ad_break_within_first_break(self):
        ds = self._make_state_with_breaks()
        ds.position = 7.5  # 7500 ms, within [0, 15000)
        assert ds.is_in_ad_break is True

    def test_is_in_ad_break_within_second_break(self):
        ds = self._make_state_with_breaks()
        ds.position = 600.0  # 600000 ms, within [527760, 1012640)
        assert ds.is_in_ad_break is True

    def test_is_in_ad_break_at_break_start(self):
        ds = self._make_state_with_breaks()
        ds.position = 527.760  # exactly 527760 ms
        assert ds.is_in_ad_break is True

    def test_is_in_ad_break_at_break_end_exclusive(self):
        ds = self._make_state_with_breaks()
        ds.position = 1012.640  # exactly 1012640 ms — end is exclusive
        assert ds.is_in_ad_break is False

    def test_is_in_ad_break_between_breaks(self):
        ds = self._make_state_with_breaks()
        ds.position = 1100.0  # 1100000 ms, between second [527760,1012640) and third [1815360,1846360)
        assert ds.is_in_ad_break is False

    def test_is_in_ad_break_after_all_breaks(self):
        ds = self._make_state_with_breaks()
        ds.position = 2000.0  # 2000000 ms, after all breaks
        assert ds.is_in_ad_break is False

    # ------------------------------------------------------------------
    # LGHorizonDeviceState.current_ad_break_end
    # ------------------------------------------------------------------

    def test_current_ad_break_end_no_breaks(self):
        ds = LGHorizonDeviceState()
        ds.position = 10.0
        assert ds.current_ad_break_end is None

    def test_current_ad_break_end_position_none(self):
        ds = self._make_state_with_breaks()
        ds.position = None
        assert ds.current_ad_break_end is None

    def test_current_ad_break_end_in_first_break(self):
        ds = self._make_state_with_breaks()
        ds.position = 7.5  # within [0, 15000)
        assert ds.current_ad_break_end == 15.0  # end_s = 15000 / 1000

    def test_current_ad_break_end_in_second_break(self):
        ds = self._make_state_with_breaks()
        ds.position = 600.0  # within [527760, 1012640)
        assert ds.current_ad_break_end == pytest.approx(1012.640)

    def test_current_ad_break_end_not_in_break(self):
        ds = self._make_state_with_breaks()
        ds.position = 1100.0  # between breaks
        assert ds.current_ad_break_end is None

    # ------------------------------------------------------------------
    # LGHorizonDeviceState.reset() clears ad_breaks
    # ------------------------------------------------------------------

    def test_reset_clears_ad_breaks(self):
        ds = self._make_state_with_breaks()
        assert len(ds.ad_breaks) == 3
        ds.reset()
        assert ds.ad_breaks == []
