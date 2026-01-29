"""LG Horizon device (set-top box) model."""

import random
import json
import urllib.parse

from typing import cast, Dict, Optional

from .models.lghorizon_device_state import LGHorizonDeviceState, LGHorizonRunningState
from .models.lghorizon_message import LGHorizonStatusMessage, LGHorizonUIStatusMessage
from .models.lghorizon_sources import (
    LGHorizonSourceType,
    LGHorizonLinearSource,
    LGHorizonVODSource,
    LGHorizonReplaySource,
    LGHorizonReviewBufferSource,
    LGHorizonNDVRSource,
)
from .models.lghorizon_auth import LGHorizonAuth
from .models.lghorizon_events import LGHorizonReplayEvent, LGHorizonVOD
from .models.lghorizon_channel import LGHorizonChannel
from .models.lghorizon_ui_status import (
    LGHorizonUIStateType,
    LGHorizonAppsState,
    LGHorizonPlayerState,
)
from .models.lghorizon_customer import LGHorizonCustomer


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

        device_state.source_type = player_state.source_type
        match player_state.source_type:
            case (
                LGHorizonSourceType.LINEAR
                | LGHorizonSourceType.REVIEWBUFFER
                | LGHorizonSourceType.NDVR
            ):
                await self._process_linear_or_reviewbuffer_state(
                    device_state, player_state
                )
            case LGHorizonSourceType.REPLAY:
                await self._process_replay_state(device_state, player_state)

            case LGHorizonSourceType.VOD:
                await self._process_vod_state(device_state, player_state)

    async def _process_apps_state(
        self,
        device_state: LGHorizonDeviceState,
        apps_state: LGHorizonAppsState,
    ) -> None:
        device_state.channel_id = apps_state.id
        device_state.title = apps_state.app_name
        device_state.image = apps_state.logo_path

    async def _process_linear_or_reviewbuffer_state(
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
        service_path = f"/v2/replayEvent/{source.event_id}?returnLinearContent=true&language={self._auth.country_code}"

        event_json = await self._auth.request(
            service_url,
            service_path,
        )
        replay_event = LGHorizonReplayEvent(event_json)
        channel = self._channels[replay_event.channel_id]
        device_state.source_type = source.source_type
        device_state.channel_id = channel.channel_number
        device_state.title = channel.title
        device_state.sub_title = replay_event.title
        if replay_event.episode_name:
            device_state.sub_title += f": {replay_event.episode_name}"

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
        service_path = f"/v2/replayEvent/{source.event_id}?returnLinearContent=true&language={self._auth.country_code}"

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
        service_path = f"/v2/detailscreen/{source.title_id}?language={self._customer.country_id}&profileId={self._profile_id}&cityId={self._customer.city_id}"

        vod_json = await self._auth.request(
            service_url,
            service_path,
        )
        vod = LGHorizonVOD(vod_json)
        device_state.title = vod.title
        device_state.title = vod.episode_title
        device_state.duration = vod.duration
        device_state.image = await self._get_intent_image_url(vod.id)
        await device_state.reset_progress()

    async def _get_intent_image_url(self, id: str) -> Optional[str]:
        """Get intent image url."""
        service_config = await self._auth.get_service_config()
        intents_url = await service_config.get_service_url("imageService")
        intents_path = "/intent"
        body_json = [
            {
                "id": id,
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
