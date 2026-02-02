"""LG Horizon device (set-top box) model."""

import random
import json
import urllib.parse
from datetime import datetime as dt, timezone

import time

from typing import cast, Dict, Optional

from .lghorizon_models import LGHorizonDeviceState, LGHorizonRunningState
from .lghorizon_models import LGHorizonStatusMessage, LGHorizonUIStatusMessage
from .lghorizon_models import (
    LGHorizonSourceType,
    LGHorizonLinearSource,
    LGHorizonVODSource,
    LGHorizonReplaySource,
    LGHorizonNDVRSource,
    LGHorizonReviewBufferSource,
    LGHorizonRecordingSource,
)
from .lghorizon_models import LGHorizonAuth
from .lghorizon_models import LGHorizonReplayEvent, LGHorizonVOD, LGHorizonVODType

from .lghorizon_models import LGHorizonRecordingSingle
from .lghorizon_models import LGHorizonChannel
from .lghorizon_models import (
    LGHorizonUIStateType,
    LGHorizonAppsState,
    LGHorizonPlayerState,
)
from .lghorizon_models import LGHorizonCustomer


class LGHorizonDeviceStateProcessor:
    """Process incoming device state messages"""

    def __init__(
        self,
        auth: LGHorizonAuth,
        channels: Dict[str, LGHorizonChannel],
        customer: LGHorizonCustomer,
        profile_id: str,
    ):
        self._auth = auth
        self._channels = channels
        self._customer = customer
        self._profile_id = profile_id

    async def process_state(
        self, device_state: LGHorizonDeviceState, status_message: LGHorizonStatusMessage
    ) -> None:
        """Process the device state based on the status message."""
        await device_state.reset()
        device_state.state = status_message.running_state

    async def process_ui_state(
        self,
        device_state: LGHorizonDeviceState,
        ui_status_message: LGHorizonUIStatusMessage,
    ) -> None:
        """Process the device state based on the UI status message."""
        await device_state.reset()
        if (
            ui_status_message.ui_state is None
            or device_state.state == LGHorizonRunningState.ONLINE_STANDBY
        ):
            await device_state.reset()
            return

        if ui_status_message.ui_state is None:
            return
        match ui_status_message.ui_state.ui_status:
            case LGHorizonUIStateType.MAINUI:
                if ui_status_message.ui_state.player_state is None:
                    return
                await self._process_main_ui_state(
                    device_state, ui_status_message.ui_state.player_state
                )
            case LGHorizonUIStateType.APPS:
                if ui_status_message.ui_state.apps_state is None:
                    return
                await self._process_apps_state(
                    device_state, ui_status_message.ui_state.apps_state
                )

        if ui_status_message.ui_state.ui_status == LGHorizonUIStateType.APPS:
            return

        if ui_status_message.ui_state.player_state is None:
            return

    async def _process_main_ui_state(
        self,
        device_state: LGHorizonDeviceState,
        player_state: LGHorizonPlayerState,
    ) -> None:
        if player_state is None:
            return
        await device_state.reset()
        device_state.source_type = player_state.source_type
        device_state.ui_state_type = LGHorizonUIStateType.MAINUI
        device_state.speed = player_state.speed

        match player_state.source_type:
            case LGHorizonSourceType.LINEAR:
                await self._process_linear_state(device_state, player_state)
            case LGHorizonSourceType.REVIEWBUFFER:
                await self._process_reviewbuffer_state(device_state, player_state)
            case LGHorizonSourceType.REPLAY:
                await self._process_replay_state(device_state, player_state)
            case LGHorizonSourceType.VOD:
                await self._process_vod_state(device_state, player_state)
            case LGHorizonSourceType.NDVR:
                await self._process_ndvr_state(device_state, player_state)

    async def _process_apps_state(
        self,
        device_state: LGHorizonDeviceState,
        apps_state: LGHorizonAppsState,
    ) -> None:
        device_state.id = apps_state.id
        device_state.show_title = apps_state.app_name
        device_state.image = apps_state.logo_path
        device_state.ui_state_type = LGHorizonUIStateType.APPS

    async def _process_linear_state(
        self,
        device_state: LGHorizonDeviceState,
        player_state: LGHorizonPlayerState,
    ) -> None:
        """Process the device state based on the UI status message."""
        if player_state.source is None:
            return
        player_state.source.__class__ = LGHorizonLinearSource
        source = cast(LGHorizonLinearSource, player_state.source)
        service_config = await self._auth.get_service_config()
        service_url = await service_config.get_service_url("linearService")
        lang = await self._customer.get_profile_lang(self._profile_id)
        service_path = f"/v2/replayEvent/{source.event_id}?returnLinearContent=true&language={lang}"

        event_json = await self._auth.request(
            service_url,
            service_path,
        )
        replay_event = LGHorizonReplayEvent(event_json)
        device_state.id = replay_event.event_id
        channel = self._channels[replay_event.channel_id]
        device_state.source_type = source.source_type
        device_state.channel_id = channel.id
        device_state.channel_name = channel.title
        device_state.episode_title = replay_event.episode_name
        device_state.season_number = replay_event.season_number
        device_state.episode_number = replay_event.episode_number
        device_state.show_title = replay_event.title
        now_in_ms = int(time.time() * 1000)

        device_state.last_position_update = int(time.time() * 1000)
        device_state.start_time = replay_event.start_time
        device_state.end_time = replay_event.end_time
        device_state.duration = replay_event.end_time - replay_event.start_time
        device_state.position = now_in_ms - int(replay_event.start_time * 1000)

        # Add random number to url to force refresh
        join_param = "?"
        if join_param in channel.stream_image:
            join_param = "&"
        image_url = (
            f"{channel.stream_image}{join_param}{str(random.randrange(1000000))}"
        )
        device_state.image = image_url

    async def _process_reviewbuffer_state(
        self,
        device_state: LGHorizonDeviceState,
        player_state: LGHorizonPlayerState,
    ) -> None:
        """Process the device state based on the UI status message."""
        if player_state.source is None:
            return
        player_state.source.__class__ = LGHorizonReviewBufferSource
        source = cast(LGHorizonReviewBufferSource, player_state.source)
        service_config = await self._auth.get_service_config()
        service_url = await service_config.get_service_url("linearService")
        lang = await self._customer.get_profile_lang(self._profile_id)
        service_path = f"/v2/replayEvent/{source.event_id}?returnLinearContent=true&language={lang}"

        event_json = await self._auth.request(
            service_url,
            service_path,
        )
        replay_event = LGHorizonReplayEvent(event_json)
        device_state.id = replay_event.event_id
        channel = self._channels[replay_event.channel_id]
        device_state.source_type = source.source_type
        device_state.channel_id = channel.id
        device_state.channel_name = channel.title
        device_state.episode_title = replay_event.episode_name
        device_state.season_number = replay_event.season_number
        device_state.episode_number = replay_event.episode_number
        device_state.show_title = replay_event.title
        device_state.last_position_update = player_state.last_speed_change_time
        device_state.position = player_state.relative_position
        device_state.start_time = replay_event.start_time
        device_state.end_time = replay_event.end_time
        device_state.duration = replay_event.end_time - replay_event.start_time
        # Add random number to url to force refresh
        join_param = "?"
        if join_param in channel.stream_image:
            join_param = "&"
        image_url = (
            f"{channel.stream_image}{join_param}{str(random.randrange(1000000))}"
        )
        device_state.image = image_url

    async def _process_replay_state(
        self,
        device_state: LGHorizonDeviceState,
        player_state: LGHorizonPlayerState,
    ) -> None:
        """Process the device state based on the UI status message."""
        if player_state.source is None:
            return
        player_state.source.__class__ = LGHorizonReplaySource
        source = cast(LGHorizonReplaySource, player_state.source)
        service_config = await self._auth.get_service_config()
        service_url = await service_config.get_service_url("linearService")
        lang = await self._customer.get_profile_lang(self._profile_id)
        service_path = f"/v2/replayEvent/{source.event_id}?returnLinearContent=true&language={lang}"

        event_json = await self._auth.request(
            service_url,
            service_path,
        )
        replay_event = LGHorizonReplayEvent(event_json)
        device_state.id = replay_event.event_id
        # Iets met buffer doen
        channel = self._channels[replay_event.channel_id]
        padding = channel.replay_pre_padding + channel.replay_post_padding
        device_state.source_type = source.source_type
        device_state.channel_id = channel.id
        device_state.episode_title = replay_event.episode_name
        device_state.season_number = replay_event.season_number
        device_state.episode_number = replay_event.episode_number
        device_state.show_title = replay_event.title
        device_state.last_position_update = int(time.time() * 1000)
        device_state.start_time = replay_event.start_time
        device_state.end_time = replay_event.end_time
        device_state.duration = (
            replay_event.end_time - replay_event.start_time + padding
        )
        device_state.position = (
            player_state.relative_position + channel.replay_pre_padding
        )
        # Add random number to url to force refresh
        device_state.image = await self._get_intent_image_url(replay_event.event_id)

    async def _process_vod_state(
        self,
        device_state: LGHorizonDeviceState,
        player_state: LGHorizonPlayerState,
    ) -> None:
        """Process the device state based on the UI status message."""
        if player_state.source is None:
            return
        player_state.source.__class__ = LGHorizonVODSource
        source = cast(LGHorizonVODSource, player_state.source)
        service_config = await self._auth.get_service_config()
        service_url = await service_config.get_service_url("vodService")
        lang = await self._customer.get_profile_lang(self._profile_id)
        service_path = f"/v2/detailscreen/{source.title_id}?language={lang}&profileId={self._profile_id}&cityId={self._customer.city_id}"

        vod_json = await self._auth.request(
            service_url,
            service_path,
        )
        vod = LGHorizonVOD(vod_json)
        device_state.id = vod.id
        if vod.vod_type == LGHorizonVODType.EPISODE:
            device_state.show_title = vod.series_title
            device_state.episode_title = vod.title
            device_state.season_number = vod.season
            device_state.episode_number = vod.episode
        else:
            device_state.show_title = vod.title

        device_state.duration = vod.duration
        device_state.last_position_update = int(time.time() * 1000)
        device_state.position = player_state.relative_position

        device_state.image = await self._get_intent_image_url(vod.id)

    async def _process_ndvr_state(
        self, device_state: LGHorizonDeviceState, player_state: LGHorizonPlayerState
    ) -> None:
        """Process the device state based on the UI status message."""
        if player_state.source is None:
            return
        player_state.source.__class__ = LGHorizonNDVRSource
        source = cast(LGHorizonNDVRSource, player_state.source)
        service_config = await self._auth.get_service_config()
        service_url = await service_config.get_service_url("recordingService")
        lang = await self._customer.get_profile_lang(self._profile_id)
        service_path = f"/customers/{self._customer.customer_id}/details/single/{source.recording_id}?profileId={self._profile_id}&language={lang}"
        recording_json = await self._auth.request(
            service_url,
            service_path,
        )
        recording = LGHorizonRecordingSingle(recording_json)
        device_state.id = recording.id
        device_state.channel_id = recording.channel_id
        if recording.channel_id:
            channel = self._channels[recording.channel_id]
            device_state.channel_name = channel.title

        device_state.episode_title = recording.episode_title
        device_state.season_number = recording.season_number
        device_state.episode_number = recording.episode_number
        device_state.last_position_update = player_state.last_speed_change_time
        device_state.position = player_state.relative_position
        if recording.start_time:
            device_state.start_time = int(
                dt.fromisoformat(
                    recording.start_time.replace("Z", "+00:00")
                ).timestamp()
            )
        if recording.end_time:
            device_state.end_time = int(
                dt.fromisoformat(recording.end_time.replace("Z", "+00:00")).timestamp()
            )
        if recording.start_time and recording.end_time:
            device_state.duration = device_state.end_time - device_state.start_time
        if recording.source == LGHorizonRecordingSource.SHOW:
            device_state.show_title = recording.title
        else:
            device_state.show_title = recording.show_title

        device_state.image = await self._get_intent_image_url(recording.id)

    async def _get_intent_image_url(self, intent_id: str) -> Optional[str]:
        """Get intent image url."""
        service_config = await self._auth.get_service_config()
        intents_url = await service_config.get_service_url("imageService")
        intents_path = "/intent"
        body_json = [
            {
                "id": intent_id,
                "intents": ["detailedBackground", "posterTile"],
            }
        ]
        intents_body = urllib.parse.quote(
            json.dumps(body_json, separators=(",", ":"), indent=None), safe="~"
        )

        # Construct the full path with the URL-encoded JSON as a query parameter
        full_intents_path = f"{intents_path}?jsonBody={intents_body}"
        intents_result = await self._auth.request(intents_url, full_intents_path)
        if (
            "intents" in intents_result[0]
            and len(intents_result[0]["intents"]) > 0
            and intents_result[0]["intents"][0]["url"]
        ):
            return intents_result[0]["intents"][0]["url"]
        return None
