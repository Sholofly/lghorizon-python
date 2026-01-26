"""LG Horizon device (set-top box) model."""

import json
import logging
from typing import Callable, Dict, Optional

from lghorizon.models.lghorizon_sources import LGHorizonSourceType

from ..const import (
    BOX_PLAY_STATE_CHANNEL,
    ONLINE_STANDBY,
    ONLINE_RUNNING,
    MEDIA_KEY_POWER,
    MEDIA_KEY_PLAY_PAUSE,
    MEDIA_KEY_STOP,
    MEDIA_KEY_CHANNEL_UP,
    MEDIA_KEY_CHANNEL_DOWN,
    MEDIA_KEY_ENTER,
    MEDIA_KEY_REWIND,
    MEDIA_KEY_FAST_FORWARD,
    MEDIA_KEY_RECORD,
    PLATFORM_TYPES,
)
from ..helpers import make_id
from .lghorizon_auth import LGHorizonAuth
from .lghorizon_channel import LGHorizonChannel
from .lghorizon_mqtt_client import LGHorizonMqttClient  # Added import for type checking
from .lghorizon_device_state import LGHorizonDeviceState
from .exceptions import LGHorizonApiConnectionError
from .lghorizon_message import LGHorizonStatusMessage, LGHorizonUIStatusMessage

# Assuming these models are available from legacy or will be moved to models/
# from ..legacy.models import (
#     # LGHorizonPlayingInfo,
#     # LGHorizonPlayerState, # This is now in lghorizon_ui_status.py
#     # LGHorizonReplayEvent,
#     # LGHorizonRecordingSingle,
#     # LGHorizonVod,
#     # LGHorizonApp,
# )

_logger = logging.getLogger(__name__)


class LGHorizonDevice:
    """The LG Horizon device (set-top box)."""

    _device_id: str
    _hashed_cpe_id: str
    _device_friendly_name: str
    _platform_type: str
    _state: Optional[str]
    _device_state: LGHorizonDeviceState
    _manufacturer: Optional[str]
    _model: Optional[str]
    _recording_capacity: Optional[int]

    _mqtt_client: LGHorizonMqttClient
    _change_callback: Callable
    _auth: LGHorizonAuth
    _channels: Dict[str, LGHorizonChannel]

    def __init__(
        self,
        device_json,
        mqtt_client: LGHorizonMqttClient,
        auth: LGHorizonAuth,
        channels: Dict[str, LGHorizonChannel],
    ):
        """Initialize the LG Horizon device."""
        self._device_id = device_json["deviceId"]
        self._hashed_cpe_id = device_json["hashedCPEId"]
        self._device_friendly_name = device_json["settings"]["deviceFriendlyName"]
        self._platform_type = device_json.get("platformType")
        self._mqtt_client = mqtt_client
        self._auth = auth
        self._channels = channels
        self._device_state = LGHorizonDeviceState()
        self._state = None  # Initialize state
        self._manufacturer = None
        self._model = None
        self._recording_capacity = None

    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self._device_id

    @property
    def platform_type(self) -> str:
        """Return the device ID."""
        return self._platform_type

    @property
    def manufacturer(self) -> str:
        """Return the manufacturer of the settop box."""
        platform_info = PLATFORM_TYPES.get(self._platform_type, dict())
        return platform_info.get("manufacturer", "unknown")

    @property
    def model(self) -> str:
        """Return the model of the settop box."""
        platform_info = PLATFORM_TYPES.get(self._platform_type, dict())
        return platform_info.get("model", "unknown")

    @property
    def is_available(self) -> bool:
        """Return the availability of the settop box."""
        return self.state == ONLINE_RUNNING or self.state == ONLINE_STANDBY

    @property
    def hashed_cpe_id(self) -> str:
        """Return the hashed CPE ID."""
        return self._hashed_cpe_id

    @property
    def device_friendly_name(self) -> str:
        """Return the device friendly name."""
        return self._device_friendly_name

    @property
    def state(self) -> Optional[str]:
        """Return the current state of the device."""
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        """Set the current state of the device."""
        self._state = value

    @property
    def device_state(self) -> LGHorizonDeviceState:
        """Return the current playing information."""
        return self._device_state

    @property
    def recording_capacity(self) -> Optional[int]:
        """Return the recording capacity used."""
        return self._recording_capacity

    @recording_capacity.setter
    def recording_capacity(self, value: int) -> None:
        """Set the recording capacity used."""
        self._recording_capacity = value

    async def update_channels(self, channels: Dict[str, LGHorizonChannel]):
        """Update the channels list."""
        self._channels = channels

    async def register_mqtt(self) -> None:
        """Register the mqtt connection."""
        if not self._mqtt_client.is_connected:
            raise LGHorizonApiConnectionError("MQTT client not connected.")
        topic = f"{self._auth.household_id}/{self._mqtt_client.client_id}/status"
        payload = {
            "source": self._mqtt_client.client_id,
            "state": ONLINE_RUNNING,
            "deviceType": "HGO",
        }
        await self._mqtt_client.publish_message(topic, json.dumps(payload))

    async def set_callback(self, change_callback: Callable) -> None:
        """Set a callback function."""
        self._change_callback = change_callback  # type: ignore [assignment] # Callback can be None

    async def handle_status_message(
        self, status_message: LGHorizonStatusMessage
    ) -> None:
        """Register a new settop box."""
        state = status_message.state
        if self._state == state:  # Access backing field for comparison
            return
        self.state = state  # Use the setter
        if self._state == ONLINE_STANDBY:  # Access backing field for comparison
            self._device_state.reset()
            if self._change_callback:
                self._change_callback(self._device_id)
        else:
            await self._request_settop_box_state()
        await self._request_settop_box_recording_capacity()

    async def handle_ui_status_message(
        self, status_message: LGHorizonUIStatusMessage
    ) -> None:
        """Handle UI status message."""
        if (
            status_message.ui_state is None
            or status_message.ui_state.player_state is None
            or status_message.ui_state.player_state.source is None
        ):
            return
        match status_message.ui_state.player_state.source.source_type:
            case LGHorizonSourceType.LINEAR:
                await self.handle_linear_message(status_message)

        await self._trigger_callback()

    async def handle_linear_message(
        self, status_message: LGHorizonUIStatusMessage
    ) -> None:
        """Handle linear UI status message."""
        pass

    async def update_recording_capacity(self, payload) -> None:
        """Updates the recording capacity."""
        if "CPE.capacity" not in payload or "used" not in payload:
            return
        self.recording_capacity = payload["used"]  # Use the setter

    # async def update_with_replay_event(
    #     self, source_type: str, event: LGHorizonReplayEvent, channel: LGHorizonChannel
    # ) -> None:
    #     """Update box with replay event."""
    #     self._device_state.source_type = source_type
    #     self._device_state.channel_id = channel.id
    #     self._device_state.channel_title = channel.title
    #     title = event.title
    #     if event.episode_name:
    #         title += f": {event.episode_name}"
    #     self._device_state.title = title
    #     self._device_state.image = channel.stream_image
    #     self._device_state.reset_progress()
    #     await self._trigger_callback()

    # async def update_with_recording(
    #     self,
    #     source_type: str,
    #     recording: LGHorizonRecordingSingle,
    #     channel: LGHorizonChannel,  # type: ignore [valid-type] # channel can be None
    #     start: float,
    #     end: float,
    #     last_speed_change: float,
    #     relative_position: float,
    # ) -> None:
    #     """Update box with recording."""
    #     self._device_state.source_type = source_type
    #     self._device_state.channel_id = channel.id
    #     self._device_state.channel_title = channel.title
    #     self._device_state.title = f"{recording.title}"
    #     self._device_state.image = recording.image
    #     start_dt = datetime.fromtimestamp(start / 1000.0)
    #     end_dt = datetime.fromtimestamp(end / 1000.0)
    #     duration = (end_dt - start_dt).total_seconds()
    #     self._device_state.duration = duration
    #     self._device_state.position = relative_position / 1000.0
    #     last_update_dt = datetime.fromtimestamp(last_speed_change / 1000.0)
    #     self._device_state.last_position_update = last_update_dt
    #     await self._trigger_callback()

    # async def update_with_vod(
    #     self,
    #     source_type: str,
    #     vod: LGHorizonVod,
    #     last_speed_change: float,
    #     relative_position: float,
    # ) -> None:
    #     """Update box with vod."""
    #     self._device_state.source_type = source_type
    #     self._device_state.channel_id = None
    #     self._device_state.channel_title = None
    #     self._device_state.title = vod.title
    #     self._device_state.image = None
    #     self._device_state.duration = vod.duration
    #     self._device_state.position = relative_position / 1000.0
    #     last_update_dt = datetime.fromtimestamp(last_speed_change / 1000.0)
    #     self._device_state.last_position_update = last_update_dt
    #     await self._trigger_callback()

    # async def update_with_app(self, source_type: str, app: LGHorizonApp) -> None:
    #     """Update box with app."""
    #     self._device_state.source_type = source_type
    #     self._device_state.channel_id = None
    #     self._device_state.channel_title = app.title
    #     self._device_state.title = app.title
    #     self._device_state.image = app.image
    #     self._device_state.reset_progress()
    #     await self._trigger_callback()

    async def _trigger_callback(self):
        if self._change_callback:
            _logger.debug("Callback called from box %s", self.device_id)
            self._change_callback(self.device_id)

    async def turn_on(self) -> None:
        """Turn the settop box on."""

        if self.state == ONLINE_STANDBY:
            await self.send_key_to_box(MEDIA_KEY_POWER)

    async def turn_off(self) -> None:
        """Turn the settop box off."""
        if self.state == ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_POWER)
            self._device_state.reset()

    async def pause(self) -> None:
        """Pause the given settopbox."""
        if self.state == ONLINE_RUNNING and not self._device_state.paused:
            await self.send_key_to_box(MEDIA_KEY_PLAY_PAUSE)

    async def play(self) -> None:
        """Resume the settopbox."""
        if self.state == ONLINE_RUNNING and self._device_state.paused:
            await self.send_key_to_box(MEDIA_KEY_PLAY_PAUSE)

    async def stop(self) -> None:
        """Stop the settopbox."""
        if self.state == ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_STOP)

    async def next_channel(self):
        """Select the next channel for given settop box."""
        if self.state == ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_CHANNEL_UP)

    async def previous_channel(self) -> None:
        """Select the previous channel for given settop box."""
        if self.state == ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_CHANNEL_DOWN)

    async def press_enter(self) -> None:
        """Press enter on the settop box."""
        if self.state == ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_ENTER)

    async def rewind(self) -> None:
        """Rewind the settop box."""
        if self.state == ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_REWIND)

    async def fast_forward(self) -> None:
        """Fast forward the settop box."""
        if self.state == ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_FAST_FORWARD)

    async def record(self):
        """Record on the settop box."""
        if self.state == ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_RECORD)

    async def set_channel(self, source: str) -> None:
        """Change te channel from the settopbox."""
        channel = [src for src in self._channels.values() if src.title == source][0]
        payload = (
            '{"id":"'
            + await make_id(8)
            + '","type":"CPE.pushToTV","source":{"clientId":"'
            + self._mqtt_client.client_id
            + '","friendlyDeviceName":"Home Assistant"},'
            + '"status":{"sourceType":"linear","source":{"channelId":"'
            + channel.id
            + '"},"relativePosition":0,"speed":1}}'
        )

        await self._mqtt_client.publish_message(
            f"{self._auth.household_id}/{self.device_id}", payload
        )

    async def play_recording(self, recording_id):
        """Play recording."""
        payload = (
            '{"id":"'
            + await make_id(8)
            + '","type":"CPE.pushToTV","source":{"clientId":"'
            + self._mqtt_client.client_id
            + '","friendlyDeviceName":"Home Assistant"},'
            + '"status":{"sourceType":"nDVR","source":{"recordingId":"'
            + recording_id
            + '"},"relativePosition":0}}'
        )
        await self._mqtt_client.publish_message(
            f"{self._auth.household_id}/{self.device_id}", payload
        )

    async def send_key_to_box(self, key: str) -> None:
        """Send emulated (remote) key press to settopbox."""
        payload_dict = {
            "type": "CPE.KeyEvent",
            "runtimeType": "key",
            "id": "ha",
            "source": self.device_id.lower(),
            "status": {"w3cKey": key, "eventType": "keyDownUp"},
        }
        payload = json.dumps(payload_dict)
        await self._mqtt_client.publish_message(
            f"{self._auth.household_id}/{self.device_id}", payload
        )

    async def _set_unknown_channel_info(self) -> None:
        """Set unknown channel info."""
        _logger.warning("Couldn't set channel. Channel info set to unknown...")
        self._device_state.source_type = BOX_PLAY_STATE_CHANNEL
        self._device_state.channel_id = None
        self._device_state.title = "No information available"
        self._device_state.image = None
        self._device_state.paused = False

    async def _request_settop_box_state(self) -> None:
        """Send mqtt message to receive state from settop box."""
        topic = f"{self._auth.household_id}/{self.device_id}"
        payload = {
            "id": await make_id(8),
            "type": "CPE.getUiStatus",
            "source": self._mqtt_client.client_id,
        }
        await self._mqtt_client.publish_message(topic, json.dumps(payload))

    async def _request_settop_box_recording_capacity(self) -> None:
        """Send mqtt message to receive state from settop box."""
        topic = f"{self._auth.household_id}/{self.device_id}"
        payload = {
            "id": await make_id(8),
            "type": "CPE.capacity",
            "source": self._mqtt_client.client_id,
        }
        await self._mqtt_client.publish_message(topic, json.dumps(payload))
