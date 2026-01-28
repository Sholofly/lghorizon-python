"""MQTT client for LGHorizon."""

import json
import logging
import asyncio
from typing import Callable, Any, Coroutine

import paho.mqtt.client as mqtt

from ..helpers import make_id
from .lghorizon_auth import LGHorizonAuth

_logger = logging.getLogger(__name__)


class LGHorizonMqttClient:
    """LGHorizon MQTT client."""

    _mqtt_broker_url: str = ""
    _mqtt_client: mqtt.Client
    _auth: LGHorizonAuth
    _mqtt_token: str = ""
    client_id: str = ""
    _on_connected_callback: Callable[[], Coroutine[Any, Any, Any]]
    _on_message_callback: Callable[[dict, str], Coroutine[Any, Any, Any]]

    @property
    def is_connected(self):
        """Is client connected."""
        return self._mqtt_client.is_connected

    def __init__(
        self,
        auth: LGHorizonAuth,
        on_connected_callback: Callable[[], Coroutine[Any, Any, Any]],
        on_message_callback: Callable[[dict, str], Coroutine[Any, Any, Any]],
    ):
        """Initialize the MQTT client."""
        self._auth = auth
        self._on_connected_callback = on_connected_callback
        self._on_message_callback = on_message_callback
        self._loop = asyncio.get_event_loop()

    @classmethod
    async def create(
        cls,
        auth: LGHorizonAuth,
        on_connected_callback: Callable[[], Coroutine[Any, Any, Any]],
        on_message_callback: Callable[[dict, str], Coroutine[Any, Any, Any]],
    ):
        """Create the MQTT client."""
        instance = cls(auth, on_connected_callback, on_message_callback)
        service_config = await auth.get_service_config()
        mqtt_broker_url = await service_config.get_service_url("mqttBroker")
        instance._mqtt_broker_url = mqtt_broker_url.replace("wss://", "").replace(
            ":443/mqtt", ""
        )
        instance.client_id = await make_id()
        instance._mqtt_client = mqtt.Client(
            client_id=instance.client_id,
            transport="websockets",
        )

        instance._mqtt_client.ws_set_options(
            headers={"Sec-WebSocket-Protocol": "mqtt, mqttv3.1, mqttv3.11"}
        )
        instance._mqtt_token = await auth.get_mqtt_token()
        instance._mqtt_client.username_pw_set(auth.household_id, instance._mqtt_token)
        instance._mqtt_client.tls_set()
        instance._mqtt_client.enable_logger(_logger)
        instance._mqtt_client.on_connect = instance._on_connect
        instance._on_connected_callback = on_connected_callback
        instance._on_message_callback = on_message_callback
        return instance

    def _on_connect(self, client, userdata, flags, result_code):  # pylint: disable=unused-argument
        if result_code == 0:
            self._mqtt_client.on_message = self._on_message
            if self._on_connected_callback:
                asyncio.run_coroutine_threadsafe(
                    self._on_connected_callback(), self._loop
                )
        elif result_code == 5:
            self._mqtt_client.username_pw_set(self._auth.household_id, self._mqtt_token)
            asyncio.run_coroutine_threadsafe(self.connect(), self._loop)
        else:
            _logger.error(
                "Cannot connect to MQTT server with resultCode: %s", result_code
            )

    def _on_message(self, client, userdata, message):  # pylint: disable=unused-argument
        """Wrapper for handling MQTT messages in a thread-safe manner."""
        asyncio.run_coroutine_threadsafe(
            self._on_client_message(client, userdata, message), self._loop
        )

    async def connect(self) -> None:
        """Connect the client."""
        self._mqtt_client.connect(self._mqtt_broker_url, 443)
        self._mqtt_client.loop_start()

    async def subscribe(self, topic: str) -> None:
        """Subscribe to a MQTT topic."""
        self._mqtt_client.subscribe(topic)

    async def publish_message(self, topic: str, json_payload: str) -> None:
        """Publish a MQTT message."""
        self._mqtt_client.publish(topic, json_payload, qos=2)

    async def disconnect(self) -> None:
        """Disconnect the client."""
        if self._mqtt_client.is_connected():
            self._mqtt_client.disconnect()

    async def _on_client_message(self, client, userdata, message):  # pylint: disable=unused-argument
        """Handle messages received by mqtt client."""
        json_payload = await self._loop.run_in_executor(
            None, json.loads, message.payload
        )
        _logger.debug(
            "Received MQTT message \n\ntopic: %s\npayload:\n\n%s\n",
            message.topic,
            json.dumps(json_payload, indent=2),
        )
        if self._on_message_callback:
            await self._on_message_callback(json_payload, message.topic)
