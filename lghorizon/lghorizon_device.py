"""LG Horizon Device."""

from __future__ import annotations
import asyncio
import json
import logging
from typing import Any, Callable, Coroutine, Dict, Optional
from .lghorizon_models import (
    LGHorizonRunningState,
    LGHorizonStatusMessage,
    LGHorizonUIStatusMessage,
    LGHorizonDeviceState,
    LGHorizonAuth,
    LGHorizonChannel,
)

from .helpers import make_id
from .lghorizon_device_state_processor import LGHorizonDeviceStateProcessor
from .lghorizon_mqtt_client import LGHorizonMqttClient
from .const import (
    MEDIA_KEY_CHANNEL_DOWN,
    MEDIA_KEY_CHANNEL_UP,
    MEDIA_KEY_ENTER,
    MEDIA_KEY_FAST_FORWARD,
    MEDIA_KEY_PLAY_PAUSE,
    MEDIA_KEY_POWER,
    MEDIA_KEY_RECORD,
    MEDIA_KEY_REWIND,
    MEDIA_KEY_STOP,
    PLATFORM_TYPES,
)

_LOGGER = logging.getLogger(__name__)


class LGHorizonDevice:
    """The LG Horizon device (set-top box)."""

    _device_id: str
    _hashed_cpe_id: str
    _device_friendly_name: str
    _platform_type: str
    _device_state: LGHorizonDeviceState
    _manufacturer: Optional[str]
    _model: Optional[str]
    _recording_capacity: Optional[int]
    _device_state_processor: LGHorizonDeviceStateProcessor
    _mqtt_client: LGHorizonMqttClient
    _change_callback: Callable[[str], Coroutine[Any, Any, Any]]
    _auth: LGHorizonAuth
    _channels: Dict[str, LGHorizonChannel]
    _last_ui_message_timestamp: int = 0

    def __init__(
        self,
        device_json,
        mqtt_client: LGHorizonMqttClient,
        device_state_processor: LGHorizonDeviceStateProcessor,
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
        self._device_state = LGHorizonDeviceState()  # Initialize state
        self._manufacturer = None
        self._model = None
        self._recording_capacity = None
        self._device_state_processor = device_state_processor
        self._change_callback = None

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
        return self._device_state.state in (
            LGHorizonRunningState.ONLINE_RUNNING,
            LGHorizonRunningState.ONLINE_STANDBY,
        )

    @property
    def hashed_cpe_id(self) -> str:
        """Return the hashed CPE ID."""
        return self._hashed_cpe_id

    @property
    def device_friendly_name(self) -> str:
        """Return the device friendly name."""
        return self._device_friendly_name

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

    @property
    def last_ui_message_timestamp(self) -> int:
        """Return the last ui message timestamp."""
        return self._last_ui_message_timestamp

    @last_ui_message_timestamp.setter
    def last_ui_message_timestamp(self, value: int) -> None:
        """Set the last ui message timestamp."""
        self._last_ui_message_timestamp = value

    async def update_channels(self, channels: Dict[str, LGHorizonChannel]):
        """Update the channels list."""
        self._channels = channels

    async def register_mqtt(self) -> None:
        """Register the mqtt connection."""
        topic = f"{self._auth.household_id}/{self._mqtt_client.client_id}/status"
        payload = {
            "source": self._mqtt_client.client_id,
            "state": LGHorizonRunningState.ONLINE_RUNNING.value,
            "deviceType": "HGO",
        }
        await self._mqtt_client.publish_message(topic, json.dumps(payload))

    async def set_callback(
        self, change_callback: Callable[[str], Coroutine[Any, Any, Any]]
    ) -> None:
        """Set a callback function to be called when the device state changes.

        Args:
            change_callback: An asynchronous callable that takes the device ID
                             as an argument.
        """
        self._change_callback = change_callback
        await self.register_mqtt()  # type: ignore [assignment] # Callback can be None
        # Always request current state from the box so we get an initial
        # UI status even when the box is already ONLINE_RUNNING at startup.
        await self._request_settop_box_state()
        await self._request_settop_box_recording_capacity()

    async def handle_status_message(
        self, status_message: LGHorizonStatusMessage
    ) -> None:
        """Handle an incoming status message from the set-top box.

        Args:
            status_message: The status message received from the device.
        """
        old_running_state = self.device_state.state
        new_running_state = status_message.running_state
        if (
            old_running_state == new_running_state
        ):  # Access backing field for comparison
            return
        await self._device_state_processor.process_state(
            self.device_state, status_message
        )  # Use the setter
        if self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING:
            await self._request_settop_box_state()

        await self._trigger_callback()
        await self._request_settop_box_recording_capacity()

    async def handle_ui_status_message(
        self, status_message: LGHorizonUIStatusMessage
    ) -> None:
        """Handle UI status message."""

        await self._device_state_processor.process_ui_state(
            self.device_state, status_message
        )
        self.last_ui_message_timestamp = status_message.message_timestamp
        await self._trigger_callback()

    async def update_recording_capacity(self, payload) -> None:
        """Updates the recording capacity."""
        if "CPE.capacity" not in payload or "used" not in payload:
            return
        self.recording_capacity = payload["used"]  # Use the setter

    async def _trigger_callback(self):
        """Trigger the registered callback function.

        This method is called when the device's state changes and a callback is set.
        """
        if self._change_callback is not None:
            _LOGGER.debug("Callback called from box %s", self.device_id)
            await self._change_callback(self.device_id)

    async def turn_on(self) -> None:
        """Turn the settop box on."""

        if self._device_state.state == LGHorizonRunningState.ONLINE_STANDBY:
            await self.send_key_to_box(MEDIA_KEY_POWER)

    async def turn_off(self) -> None:
        """Turn the settop box off."""
        if self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_POWER)
            self._device_state.reset()

    async def pause(self) -> None:
        """Pause the given settopbox."""
        if (
            self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING
            and not self._device_state.paused
        ):
            await self.send_key_to_box(MEDIA_KEY_PLAY_PAUSE)

    async def play(self) -> None:
        """Resume the settopbox."""
        if (
            self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING
            and self._device_state.paused
        ):
            await self.send_key_to_box(MEDIA_KEY_PLAY_PAUSE)

    async def stop(self) -> None:
        """Stop the settopbox."""
        if self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_STOP)

    async def next_channel(self):
        """Select the next channel for given settop box."""
        if self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_CHANNEL_UP)

    async def previous_channel(self) -> None:
        """Select the previous channel for given settop box."""
        if self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_CHANNEL_DOWN)

    async def press_enter(self) -> None:
        """Press enter on the settop box."""
        if self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_ENTER)

    async def rewind(self) -> None:
        """Rewind the settop box."""
        if self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_REWIND)

    async def fast_forward(self) -> None:
        """Fast forward the settop box."""
        if self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_FAST_FORWARD)

    async def record(self):
        """Record on the settop box."""
        if self._device_state.state == LGHorizonRunningState.ONLINE_RUNNING:
            await self.send_key_to_box(MEDIA_KEY_RECORD)

    async def set_player_position(self, position: int) -> None:
        """Set the player position on the settop box."""
        payload = {
            "source": self.device_id,
            "type": "CPE.setPlayerPosition",
            "runtimeType": "setPlayerposition",
            "id": make_id(),
            "version": "1.3.11",
            "status": {"relativePosition": position},
        }
        payload_str = json.dumps(payload)
        await self._mqtt_client.publish_message(
            f"{self._auth.household_id}/{self.device_id}", payload_str
        )

    async def display_message(self, sourceType: str, message: str) -> None:
        """Display a message on the set-top box and repeat it for longer visibility.

        # We sturen de payload 3 keer met een kortere tussentijd

        This method sends the message payload multiple times to ensure it stays
        visible on the screen for a longer duration, as the display time for
        such messages is typically short.

        Args:
            sourceType: The type of source for the message (e.g., "linear").
            message: The message string to display.
        """
        for i in range(3):
            payload = {
                "id": make_id(8),
                "type": "CPE.pushToTV",
                "source": {
                    "clientId": self._mqtt_client.client_id,
                    "friendlyDeviceName": f"\n\n{message}",
                },
                "status": {
                    "sourceType": sourceType,
                    "source": {"channelId": "1234"},
                    "title": "Nieuwe melding",
                    "relativePosition": 0,
                    "speed": 1,
                },
            }

            await self._mqtt_client.publish_message(
                f"{self._auth.household_id}/{self.device_id}", json.dumps(payload)
            )

            # Omdat de melding 3 seconden blijft staan, wachten we 3 seconden
            # voor de volgende 'refresh'.
            if i < 2:
                await asyncio.sleep(3)

    async def set_channel(self, source: str) -> None:
        """Change te channel from the settopbox."""
        channel = next(
            (src for src in self._channels.values() if src.title == source), None
        )
        if channel is None:
            raise ValueError(f"Channel '{source}' not found")
        payload = {
            "id": make_id(8),
            "type": "CPE.pushToTV",
            "source": {
                "clientId": self._mqtt_client.client_id,
                "friendlyDeviceName": "Home Assistant",
            },
            "status": {
                "sourceType": "linear",
                "source": {"channelId": channel.id},
                "relativePosition": 0,
                "speed": 1,
            },
        }

        await self._mqtt_client.publish_message(
            f"{self._auth.household_id}/{self.device_id}", json.dumps(payload)
        )

    async def play_recording(self, recording_id):
        """Play recording."""
        payload = {
            "id": make_id(8),
            "type": "CPE.pushToTV",
            "source": {
                "clientId": self._mqtt_client.client_id,
                "friendlyDeviceName": "Home Assistant",
            },
            "status": {
                "sourceType": "nDVR",
                "source": {"recordingId": recording_id},
                "relativePosition": 0,
            },
        }

        await self._mqtt_client.publish_message(
            f"{self._auth.household_id}/{self.device_id}", json.dumps(payload)
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

    async def _request_settop_box_state(self) -> None:
        """Send mqtt message to receive state from settop box."""
        topic = f"{self._auth.household_id}/{self.device_id}"
        payload = {
            "id": make_id(8),
            "type": "CPE.getUiStatus",
            "source": self._mqtt_client.client_id,
        }
        await self._mqtt_client.publish_message(topic, json.dumps(payload))

    async def _request_settop_box_recording_capacity(self) -> None:
        """Send mqtt message to receive state from settop box."""
        topic = f"{self._auth.household_id}/{self.device_id}"
        payload = {
            "id": make_id(8),
            "type": "CPE.capacity",
            "source": self._mqtt_client.client_id,
        }
        await self._mqtt_client.publish_message(topic, json.dumps(payload))
