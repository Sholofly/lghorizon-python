import asyncio
import json
import logging
from typing import Any, Callable, Coroutine

import paho.mqtt.client as mqtt

from .helpers import make_id
from .lghorizon_models import LGHorizonAuth

_logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 10.0
MAX_RECONNECT_DELAY = 60

# CONNACK refusals caused by an expired or rejected token. Paho 1.x reports the
# MQTT 3.1.1 return codes, paho 2.x the equivalent MQTT 5 reason codes.
_AUTH_FAILURE_CODES = (4, 5, 134, 135)


def _reason_code_value(reason_code: Any) -> int:
    """Return the numeric value of a paho reason code or a plain int."""
    return getattr(reason_code, "value", reason_code)


class LGHorizonMqttClient:
    """Asynchronous-friendly wrapper around Paho MQTT."""

    def __init__(
        self,
        auth: LGHorizonAuth,
        on_connected_callback: Callable[[], Coroutine[Any, Any, Any]],
        on_message_callback: Callable[[dict, str], Coroutine[Any, Any, Any]],
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """Initialize the LGHorizonMqttClient.

        Args:
            auth: The authentication object for obtaining MQTT tokens.
            on_connected_callback: An async callback function for MQTT connection events.
            on_message_callback: An async callback function for MQTT message events.
            loop: The asyncio event loop.
        """
        self._auth = auth
        self._on_connected_callback = on_connected_callback
        self._on_message_callback = on_message_callback
        self._loop = loop

        self._mqtt_client: mqtt.Client | None = None
        self._mqtt_broker_url: str = ""
        self._mqtt_token: str = ""
        self.client_id: str = ""
        self._reconnect_task: asyncio.Task | None = None
        self._disconnect_requested: bool = False

        # FIFO queues
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._publish_queue: asyncio.Queue = asyncio.Queue()

        # Worker tasks
        self._message_worker_task: asyncio.Task | None = None
        self._publish_worker_task: asyncio.Task | None = None

    @property
    def is_connected(self) -> bool:
        return self._mqtt_client is not None and self._mqtt_client.is_connected()

    @classmethod
    async def create(
        cls,
        auth: LGHorizonAuth,
        on_connected_callback: Callable[[], Coroutine[Any, Any, Any]],
        on_message_callback: Callable[[dict, str], Coroutine[Any, Any, Any]],
    ) -> "LGHorizonMqttClient":
        """Asynchronously create and initialize an LGHorizonMqttClient instance."""

        loop = asyncio.get_running_loop()
        instance = cls(auth, on_connected_callback, on_message_callback, loop)

        # Fetch the service config
        service_config = await auth.get_service_config()
        mqtt_broker_url = service_config.get_service_url("mqttBroker")
        instance._mqtt_broker_url = mqtt_broker_url.replace("wss://", "").replace(
            ":443/mqtt", ""
        )

        instance.client_id = make_id()

        # Paho client
        # Reconnects are handled by _reconnect_loop so that each attempt uses
        # a fresh token instead of the credentials paho captured at connect.
        instance._mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=instance.client_id,
            transport="websockets",
            reconnect_on_failure=False,
        )
        instance._mqtt_client.ws_set_options(
            headers={"Sec-WebSocket-Protocol": "mqtt, mqttv3.1, mqttv3.11"}
        )

        # Fetch the MQTT token
        instance._mqtt_token = await auth.get_mqtt_token()
        instance._mqtt_client.username_pw_set(
            auth.household_id,
            instance._mqtt_token,
        )

        # Set up TLS (blocking → executor)
        await loop.run_in_executor(None, instance._mqtt_client.tls_set)

        instance._mqtt_client.enable_logger(_logger)
        instance._mqtt_client.on_connect = instance._on_connect
        instance._mqtt_client.on_message = instance._on_message
        instance._mqtt_client.on_disconnect = instance._on_disconnect

        return instance

    async def connect(self) -> None:
        """Connect the MQTT client to the broker asynchronously."""
        if not self._mqtt_client:
            raise RuntimeError("MQTT client not initialized")

        if self.is_connected:
            _logger.debug("MQTT client is already connected.")
            return

        self._disconnect_requested = False  # Reset flag for new connection attempt

        # Cancel any ongoing reconnect task if connect() is called manually
        if self._reconnect_task and not self._reconnect_task.done():
            _logger.debug("Cancelling existing reconnect task before manual connect.")
            self._reconnect_task.cancel()
            self._reconnect_task = None

        _logger.debug("Attempting initial MQTT connection...")
        await self._connect()

    async def _connect(self) -> None:
        """Open the connection and (re)start the Paho thread and workers."""
        # Blocking connect → executor
        await self._loop.run_in_executor(
            None,
            self._mqtt_client.connect,
            self._mqtt_broker_url,
            443,
        )

        # Start Paho thread
        self._mqtt_client.loop_start()

        # Stop existing workers before starting new ones
        if self._message_worker_task and not self._message_worker_task.done():
            self._message_worker_task.cancel()
        if self._publish_worker_task and not self._publish_worker_task.done():
            self._publish_worker_task.cancel()

        # Start workers
        self._message_worker_task = asyncio.create_task(self._message_worker())
        self._publish_worker_task = asyncio.create_task(self._publish_worker())

    async def disconnect(self) -> None:
        """Disconnect the MQTT client from the broker asynchronously."""
        if not self._mqtt_client:
            return

        self._disconnect_requested = True

        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None

        # Stop workers
        if self._message_worker_task:
            self._message_worker_task.cancel()
            self._message_worker_task = None

        if self._publish_worker_task:
            self._publish_worker_task.cancel()
            self._publish_worker_task = None

        # Blocking disconnect → executor
        await self._loop.run_in_executor(None, self._mqtt_client.disconnect)
        self._mqtt_client.loop_stop()

    async def subscribe(self, topic: str) -> None:
        """Subscribe to an MQTT topic.

        Args:
            topic: The MQTT topic to subscribe to.
        """
        if not self._mqtt_client:
            raise RuntimeError("MQTT client not initialized")

        self._mqtt_client.subscribe(topic)

    async def publish_message(self, topic: str, json_payload: str) -> None:
        """Queue an MQTT message for publishing.

        Args:
            topic: The MQTT topic to publish to.
            json_payload: The JSON payload as a string.
        """
        await self._publish_queue.put((topic, json_payload))

    # -------------------------
    # INTERNAL CALLBACKS
    # -------------------------

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Callback for when the MQTT client connects to the broker.

        Args:
            client: The Paho MQTT client instance.
            userdata: User data passed to the client.
            flags: Response flags from the broker.
            reason_code: The connection result.
            properties: MQTT 5 properties (unused).
        """
        code = _reason_code_value(reason_code)
        if code == 0:
            _logger.debug("MQTT client connected successfully.")
            self._loop.call_soon_threadsafe(self._cancel_reconnect_task)
            asyncio.run_coroutine_threadsafe(
                self._on_connected_callback(),
                self._loop,
            )
            return

        if code in _AUTH_FAILURE_CODES:
            _logger.debug("MQTT connection refused: token rejected or expired.")
        else:
            _logger.error("MQTT connect error: %s", reason_code)
        self._schedule_reconnect()

    def _on_message(self, client, userdata, message):
        """Callback for when an MQTT message is received.

        Args:
            client: The Paho MQTT client instance.
            userdata: User data passed to the client.
            message: The MQTTMessage object containing topic and payload.
        """
        asyncio.run_coroutine_threadsafe(
            self._message_queue.put((message.topic, message.payload)),
            self._loop,
        )

    def _on_disconnect(
        self, client, userdata, disconnect_flags, reason_code=None, properties=None
    ):
        """Callback for when the MQTT client disconnects from the broker.

        Args:
            client: The Paho MQTT client instance.
            userdata: User data passed to the client.
            disconnect_flags: Disconnect flags from the broker.
            reason_code: The disconnection result.
            properties: MQTT 5 properties (unused).
        """
        _logger.warning("MQTT disconnected with result code: %s", reason_code)
        if not self._disconnect_requested:
            _logger.debug("Unexpected MQTT disconnection. Initiating reconnect loop.")
            self._schedule_reconnect()
        else:
            _logger.debug("MQTT disconnected as requested.")

    def _schedule_reconnect(self):
        """Start the reconnect loop from any thread unless one is active."""
        if not self._reconnect_task or self._reconnect_task.done():
            self._loop.call_soon_threadsafe(self._start_reconnect_task)
        else:
            _logger.debug("Reconnect loop already active.")

    def _cancel_reconnect_task(self):
        """Cancel a running reconnect loop (event loop thread only)."""
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None

    def _start_reconnect_task(self):
        """Start the reconnect loop as an asyncio.Task (must be called from the event loop thread)."""
        if self._disconnect_requested:
            return
        if self._reconnect_task and not self._reconnect_task.done():
            return
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _refresh_mqtt_token(self) -> None:
        """Fetch a new MQTT token and use it for the next connection attempt."""
        self._mqtt_token = await self._auth.get_mqtt_token()
        self._mqtt_client.username_pw_set(self._auth.household_id, self._mqtt_token)

    async def _wait_until_connected(self) -> bool:
        """Wait for the broker to accept the connection."""
        deadline = self._loop.time() + CONNECT_TIMEOUT
        while self._loop.time() < deadline:
            if self.is_connected:
                return True
            await asyncio.sleep(0.1)
        return self.is_connected

    async def _reconnect_loop(self):
        """Manages the MQTT reconnection process with exponential backoff."""
        retries = 0
        try:
            while not self._disconnect_requested:
                if self.is_connected:
                    _logger.debug(
                        "MQTT client reconnected within loop, stopping reconnect attempts."
                    )
                    break

                delay = min(2**retries, MAX_RECONNECT_DELAY)
                _logger.debug(
                    "Waiting %s seconds before MQTT reconnect attempt %s",
                    delay,
                    retries + 1,
                )
                await asyncio.sleep(delay)
                if self._disconnect_requested:
                    break

                try:
                    _logger.debug("Attempting MQTT reconnect...")
                    await self._refresh_mqtt_token()
                    # Paho's thread ends after a disconnect; join it before
                    # loop_start() so the new thread is not silently skipped.
                    await self._loop.run_in_executor(None, self._mqtt_client.loop_stop)
                    await self._connect()
                    if await self._wait_until_connected():
                        break
                    _logger.warning("MQTT broker did not accept the connection in time")
                except Exception as e:
                    _logger.error("MQTT reconnect attempt failed: %s", e)
                retries += 1
        finally:
            if self._reconnect_task is asyncio.current_task():
                self._reconnect_task = None

    # -------------------------
    # MESSAGE WORKER (FIFO)
    # -------------------------

    async def _message_worker(self):
        """Worker task to process incoming MQTT messages from the queue."""
        while True:
            topic, payload = await self._message_queue.get()

            try:
                json_payload = json.loads(payload)
                await self._on_message_callback(json_payload, topic)
            except Exception:
                _logger.exception("Error processing MQTT message")

            self._message_queue.task_done()

    # -------------------------
    # PUBLISH WORKER (FIFO)
    # -------------------------

    async def _publish_worker(self):
        """Worker task to process outgoing MQTT publish commands from the queue."""
        while True:
            topic, payload = await self._publish_queue.get()

            try:
                # Wait until MQTT is really connected
                while not self.is_connected:
                    await asyncio.sleep(0.1)

                # Publish is non-blocking
                self._mqtt_client.publish(topic, payload, qos=2)

            except Exception:
                _logger.exception("Error publishing MQTT message")

            self._publish_queue.task_done()
