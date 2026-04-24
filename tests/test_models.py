"""Comprehensive unit tests for lghorizon/lghorizon_models.py."""

from __future__ import annotations

import pytest

from lghorizon.lghorizon_models import (
    LGHorizonAppsState,
    LGHorizonChannel,
    LGHorizonCustomer,
    LGHorizonDeviceState,
    LGHorizonEntitlements,
    LGHorizonLinearSource,
    LGHorizonMediaType,
    LGHorizonMessageType,
    LGHorizonNDVRSource,
    LGHorizonPlayerState,
    LGHorizonProfile,
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
        lang = await c.get_profile_lang("profile-2")
        assert lang == "en"

    async def test_get_profile_lang_default_nl(self, sample_customer_json):
        c = LGHorizonCustomer(sample_customer_json)
        lang = await c.get_profile_lang("nonexistent-profile")
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

    async def test_reset_clears_all_fields(self):
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

        await ds.reset()

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

    async def test_reset_progress_clears_only_progress(self):
        ds = LGHorizonDeviceState()
        ds.channel_id = "ch-1"
        ds.duration = 1800.0
        ds.position = 900.0
        ds.last_position_update = 12345

        await ds.reset_progress()

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
        assert ps.last_speed_change_time == 1700000000

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
        assert msg.message_timestamp == 1700000000

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
        assert ev.start_time == 1700000000

    def test_end_time(self, sample_replay_event_json):
        ev = LGHorizonReplayEvent(sample_replay_event_json)
        assert ev.end_time == 1700003600

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
        url = await sample_service_config.get_service_url("linearService")
        assert url == "https://linear.example.com"

    async def test_get_service_url_raises_for_unknown(self, sample_service_config):
        with pytest.raises(ValueError):
            await sample_service_config.get_service_url("nonExistentService")

    async def test_get_all_services(self, sample_service_config):
        services = await sample_service_config.get_all_services()
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
