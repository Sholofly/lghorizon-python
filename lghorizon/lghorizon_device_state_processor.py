"""LG Horizon device (set-top box) model."""

import random
import json
import urllib.parse

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
)
from .lghorizon_models import LGHorizonAuth
from .lghorizon_models import (
    LGHorizonReplayEvent,
    LGHorizonVOD,
)

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
        device_state.channel_id = apps_state.id
        device_state.title = apps_state.app_name
        device_state.image = apps_state.logo_path

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
        channel = self._channels[replay_event.channel_id]
        device_state.source_type = source.source_type
        device_state.channel_id = channel.channel_number
        device_state.channel_name = channel.title
        device_state.title = replay_event.title
        device_state.sub_title = replay_event.full_episode_title

        # Add random number to url to force refresh
        join_param = "?"
        if join_param in channel.stream_image:
            join_param = "&"
        image_url = (
            f"{channel.stream_image}{join_param}{str(random.randrange(1000000))}"
        )
        device_state.image = image_url
        await device_state.reset_progress()

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
        channel = self._channels[replay_event.channel_id]
        device_state.source_type = source.source_type
        device_state.channel_id = channel.channel_number
        device_state.channel_name = channel.title
        device_state.title = replay_event.title
        device_state.sub_title = replay_event.full_episode_title

        # Add random number to url to force refresh
        join_param = "?"
        if join_param in channel.stream_image:
            join_param = "&"
        image_url = (
            f"{channel.stream_image}{join_param}{str(random.randrange(1000000))}"
        )
        device_state.image = image_url
        await device_state.reset_progress()

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
        device_state.source_type = source.source_type
        device_state.channel_id = None
        device_state.title = replay_event.title
        if replay_event.full_episode_title:
            device_state.sub_title = replay_event.full_episode_title

        # Add random number to url to force refresh
        device_state.image = await self._get_intent_image_url(replay_event.event_id)
        await device_state.reset_progress()

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
        device_state.title = vod.title
        device_state.sub_title = vod.full_episode_title
        device_state.duration = vod.duration
        device_state.image = await self._get_intent_image_url(vod.id)
        await device_state.reset_progress()

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
        device_state.title = recording.title
        device_state.sub_title = recording.full_episode_title
        device_state.channel_id = recording.channel_id
        if recording.channel_id:
            channel = self._channels[recording.channel_id]
            device_state.channel_name = channel.title

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
