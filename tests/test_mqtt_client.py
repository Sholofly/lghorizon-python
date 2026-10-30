"""Unit tests for LGHorizonMqttClient."""

import asyncio
import paho.mqtt.client as mqtt
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from lghorizon.lghorizon_mqtt_client import LGHorizonMqttClient


# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

BROKER_URL_RAW = "wss://mqtt.example.com:443/mqtt"
BROKER_URL_STRIPPED = "mqtt.example.com"
MQTT_TOKEN = "mqtt-token-xyz"
HOUSEHOLD_ID = "household-123"


def _make_mock_auth():
    """Return a fully-configured mock auth object."""
    auth = MagicMock()
    auth.household_id = HOUSEHOLD_ID

    service_config = MagicMock()
    service_config.get_service_url = MagicMock(return_value=BROKER_URL_RAW)

    auth.get_service_config = AsyncMock(return_value=service_config)
    auth.get_mqtt_token = AsyncMock(return_value=MQTT_TOKEN)
    auth.fetch_access_token = AsyncMock()
    return auth


def _make_paho_mock():
    """Return a MagicMock that looks like a paho.mqtt.client.Client instance."""
    mock = MagicMock()
    mock.is_connected.return_value = False
    mock.connect = MagicMock()
    mock.loop_start = MagicMock()
    mock.loop_stop = MagicMock()
    mock.disconnect = MagicMock()
    mock.subscribe = MagicMock()
    mock.publish = MagicMock()
    mock.tls_set = MagicMock()
    mock.username_pw_set = MagicMock()
    mock.ws_set_options = MagicMock()
    mock.enable_logger = MagicMock()
    return mock


async def _create_client(paho_instance=None):
    """Helper: create an LGHorizonMqttClient via the factory, patching Paho."""
    auth = _make_mock_auth()
    on_connected = AsyncMock()
    on_message = AsyncMock()

    if paho_instance is None:
        paho_instance = _make_paho_mock()

    with patch(
        "lghorizon.lghorizon_mqtt_client.mqtt.Client", return_value=paho_instance
    ):
        # tls_set is called via run_in_executor; patch executor to call it synchronously
        with patch(
            "asyncio.AbstractEventLoop.run_in_executor",
            new=AsyncMock(return_value=None),
        ):
            client = await LGHorizonMqttClient.create(auth, on_connected, on_message)

    return client, auth, on_connected, on_message, paho_instance


def _make_direct_client(loop=None):
    """Directly instantiate LGHorizonMqttClient (bypasses create())."""
    if loop is None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop (e.g. in a synchronous test), so create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    auth = _make_mock_auth()
    on_connected = AsyncMock()
    on_message = AsyncMock()
    return (
        LGHorizonMqttClient(auth, on_connected, on_message, loop),
        auth,
        on_connected,
        on_message,
    )


# ===========================================================================
# create() factory tests
# ===========================================================================


class TestCreate:
    async def test_returns_instance(self):
        paho_mock = _make_paho_mock()
        with patch(
            "lghorizon.lghorizon_mqtt_client.mqtt.Client", return_value=paho_mock
        ):
            with patch(
                "asyncio.AbstractEventLoop.run_in_executor",
                new=AsyncMock(return_value=None),
            ):
                auth = _make_mock_auth()
                client = await LGHorizonMqttClient.create(
                    auth, AsyncMock(), AsyncMock()
                )

        assert isinstance(client, LGHorizonMqttClient)

    async def test_client_id_is_non_empty_string(self):
        paho_mock = _make_paho_mock()
        with patch(
            "lghorizon.lghorizon_mqtt_client.mqtt.Client", return_value=paho_mock
        ):
            with patch(
                "asyncio.AbstractEventLoop.run_in_executor",
                new=AsyncMock(return_value=None),
            ):
                auth = _make_mock_auth()
                client = await LGHorizonMqttClient.create(
                    auth, AsyncMock(), AsyncMock()
                )

        assert isinstance(client.client_id, str)
        assert len(client.client_id) > 0

    async def test_broker_url_strips_wss_and_port(self):
        paho_mock = _make_paho_mock()
        with patch(
            "lghorizon.lghorizon_mqtt_client.mqtt.Client", return_value=paho_mock
        ):
            with patch(
                "asyncio.AbstractEventLoop.run_in_executor",
                new=AsyncMock(return_value=None),
            ):
                auth = _make_mock_auth()
                client = await LGHorizonMqttClient.create(
                    auth, AsyncMock(), AsyncMock()
                )

        assert client._mqtt_broker_url == BROKER_URL_STRIPPED

    async def test_username_password_set_from_auth(self):
        paho_mock = _make_paho_mock()
        with patch(
            "lghorizon.lghorizon_mqtt_client.mqtt.Client", return_value=paho_mock
        ):
            with patch(
                "asyncio.AbstractEventLoop.run_in_executor",
                new=AsyncMock(return_value=None),
            ):
                auth = _make_mock_auth()
                await LGHorizonMqttClient.create(auth, AsyncMock(), AsyncMock())

        paho_mock.username_pw_set.assert_called_once_with(HOUSEHOLD_ID, MQTT_TOKEN)

    async def test_paho_client_constructed_with_client_id(self):
        paho_mock = _make_paho_mock()
        with patch(
            "lghorizon.lghorizon_mqtt_client.mqtt.Client", return_value=paho_mock
        ) as mock_cls:
            with patch(
                "asyncio.AbstractEventLoop.run_in_executor",
                new=AsyncMock(return_value=None),
            ):
                auth = _make_mock_auth()
                client = await LGHorizonMqttClient.create(
                    auth, AsyncMock(), AsyncMock()
                )

        call_kwargs = mock_cls.call_args
        # client_id should be set and match the instance's client_id
        assert call_kwargs.kwargs.get("client_id") == client.client_id or (
            len(call_kwargs.args) > 0 and call_kwargs.args[0] == client.client_id
        )


# ===========================================================================
# connect() tests
# ===========================================================================


class TestConnect:
    async def test_raises_if_not_initialized(self):
        client, *_ = _make_direct_client()
        # _mqtt_client is None by default
        with pytest.raises(RuntimeError, match="MQTT client not initialized"):
            await client.connect()

    async def test_calls_connect_with_broker_url_and_port_443(self):
        loop = asyncio.get_running_loop()
        client, auth, on_connected, on_message = _make_direct_client(loop)
        paho_mock = _make_paho_mock()
        client._mqtt_client = paho_mock
        client._mqtt_broker_url = BROKER_URL_STRIPPED

        with patch.object(
            loop, "run_in_executor", new=AsyncMock(return_value=None)
        ) as mock_exec:
            await client.connect()
        client._message_worker_task.cancel()
        client._publish_worker_task.cancel()

        # run_in_executor should have been called with connect, broker url, port 443
        call_args_list = mock_exec.call_args_list
        connect_call = next(
            (c for c in call_args_list if c.args[1] == paho_mock.connect), None
        )
        assert connect_call is not None, "connect was not called via run_in_executor"
        assert connect_call.args[2] == BROKER_URL_STRIPPED
        assert connect_call.args[3] == 443

    async def test_calls_loop_start(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)
        paho_mock = _make_paho_mock()
        client._mqtt_client = paho_mock
        client._mqtt_broker_url = BROKER_URL_STRIPPED

        with patch.object(loop, "run_in_executor", new=AsyncMock(return_value=None)):
            await client.connect()
        client._message_worker_task.cancel()
        client._publish_worker_task.cancel()

        paho_mock.loop_start.assert_called_once()

    async def test_creates_worker_tasks(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)
        paho_mock = _make_paho_mock()
        client._mqtt_client = paho_mock
        client._mqtt_broker_url = BROKER_URL_STRIPPED

        with patch.object(loop, "run_in_executor", new=AsyncMock(return_value=None)):
            await client.connect()

        assert client._message_worker_task is not None
        assert client._publish_worker_task is not None
        # Clean up tasks
        client._message_worker_task.cancel()
        client._publish_worker_task.cancel()

    async def test_skips_if_already_connected(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)
        paho_mock = _make_paho_mock()
        paho_mock.is_connected.return_value = True
        client._mqtt_client = paho_mock
        client._mqtt_broker_url = BROKER_URL_STRIPPED

        with patch.object(
            loop, "run_in_executor", new=AsyncMock(return_value=None)
        ) as mock_exec:
            await client.connect()

        # connect should NOT have been called via executor
        connect_calls = [
            c
            for c in mock_exec.call_args_list
            if len(c.args) > 1 and c.args[1] == paho_mock.connect
        ]
        assert len(connect_calls) == 0


# ===========================================================================
# disconnect() tests
# ===========================================================================


class TestDisconnect:
    async def test_returns_gracefully_if_no_mqtt_client(self):
        client, *_ = _make_direct_client()
        # Should not raise
        await client.disconnect()

    async def test_sets_disconnect_requested(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)
        paho_mock = _make_paho_mock()
        client._mqtt_client = paho_mock

        with patch.object(loop, "run_in_executor", new=AsyncMock(return_value=None)):
            await client.disconnect()

        assert client._disconnect_requested is True

    async def test_cancels_worker_tasks(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)
        paho_mock = _make_paho_mock()
        client._mqtt_client = paho_mock

        msg_task = MagicMock(spec=asyncio.Task)
        pub_task = MagicMock(spec=asyncio.Task)
        client._message_worker_task = msg_task
        client._publish_worker_task = pub_task

        with patch.object(loop, "run_in_executor", new=AsyncMock(return_value=None)):
            await client.disconnect()

        msg_task.cancel.assert_called_once()
        pub_task.cancel.assert_called_once()

    async def test_calls_disconnect_and_loop_stop(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)
        paho_mock = _make_paho_mock()
        client._mqtt_client = paho_mock

        with patch.object(loop, "run_in_executor", new=AsyncMock(return_value=None)):
            await client.disconnect()

        paho_mock.loop_stop.assert_called_once()


# ===========================================================================
# subscribe() tests
# ===========================================================================


class TestSubscribe:
    async def test_calls_subscribe_with_topic(self):
        client, *_ = _make_direct_client()
        paho_mock = _make_paho_mock()
        client._mqtt_client = paho_mock

        await client.subscribe("test/topic")

        paho_mock.subscribe.assert_called_once_with("test/topic")

    async def test_raises_if_not_initialized(self):
        client, *_ = _make_direct_client()
        with pytest.raises(RuntimeError, match="MQTT client not initialized"):
            await client.subscribe("test/topic")


# ===========================================================================
# publish_message() tests
# ===========================================================================


class TestPublishMessage:
    async def test_puts_message_on_publish_queue(self):
        client, *_ = _make_direct_client()
        await client.publish_message("test/topic", '{"key": "value"}')

        assert client._publish_queue.qsize() == 1
        topic, payload = await client._publish_queue.get()
        assert topic == "test/topic"
        assert payload == '{"key": "value"}'


# ===========================================================================
# is_connected property tests
# ===========================================================================


class TestIsConnected:
    def test_returns_false_when_mqtt_client_is_none(self):
        client, *_ = _make_direct_client()
        assert client._mqtt_client is None
        assert client.is_connected is False

    def test_returns_true_when_paho_is_connected(self):
        client, *_ = _make_direct_client()
        paho_mock = _make_paho_mock()
        paho_mock.is_connected.return_value = True
        client._mqtt_client = paho_mock

        assert client.is_connected is True

    def test_returns_false_when_paho_not_connected(self):
        client, *_ = _make_direct_client()
        paho_mock = _make_paho_mock()
        paho_mock.is_connected.return_value = False
        client._mqtt_client = paho_mock

        assert client.is_connected is False


# ===========================================================================
# _on_connect callback tests
# ===========================================================================


class TestOnConnect:
    async def test_result_code_0_calls_on_connected_callback(self):
        loop = asyncio.get_running_loop()
        client, auth, on_connected, on_message = _make_direct_client(loop)

        with patch("asyncio.run_coroutine_threadsafe") as mock_rct:
            client._on_connect(MagicMock(), None, {}, 0)

        mock_rct.assert_called_once()
        # First arg should be the coroutine from on_connected_callback(), second is loop
        assert mock_rct.call_args.args[1] is loop

    async def test_result_code_0_cancels_reconnect_task(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)

        reconnect_task = MagicMock(spec=asyncio.Task)
        client._reconnect_task = reconnect_task

        with patch("asyncio.run_coroutine_threadsafe"):
            client._on_connect(MagicMock(), None, {}, 0)
        await asyncio.sleep(0)

        reconnect_task.cancel.assert_called_once()
        assert client._reconnect_task is None

    @pytest.mark.parametrize("code", [4, 5, 134, 135, 3, 136])
    async def test_refused_connection_schedules_reconnect(self, code: int):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)

        with patch.object(loop, "call_soon_threadsafe") as mock_cst:
            client._on_connect(MagicMock(), None, {}, code)

        mock_cst.assert_called_once_with(client._start_reconnect_task)

    async def test_reason_code_object_is_supported(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)

        with patch("asyncio.run_coroutine_threadsafe") as mock_rct:
            client._on_connect(MagicMock(), None, MagicMock(), MagicMock(value=0), None)

        mock_rct.assert_called_once()


# ===========================================================================
# _on_disconnect callback tests
# ===========================================================================


class TestOnDisconnect:
    async def test_starts_reconnect_if_not_disconnect_requested(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)
        client._disconnect_requested = False
        client._reconnect_task = None

        with patch.object(loop, "call_soon_threadsafe") as mock_cst:
            client._on_disconnect(MagicMock(), None, MagicMock(), 1, None)

        mock_cst.assert_called_once_with(client._start_reconnect_task)

    async def test_does_not_start_reconnect_if_disconnect_requested(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)
        client._disconnect_requested = True

        with patch.object(loop, "call_soon_threadsafe") as mock_cst:
            client._on_disconnect(MagicMock(), None, MagicMock(), 0, None)

        mock_cst.assert_not_called()

    async def test_does_not_start_reconnect_if_task_already_running(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_direct_client(loop)
        client._disconnect_requested = False

        running_task = MagicMock(spec=asyncio.Task)
        running_task.done.return_value = False
        client._reconnect_task = running_task

        with patch.object(loop, "call_soon_threadsafe") as mock_cst:
            client._on_disconnect(MagicMock(), None, MagicMock(), 1, None)

        mock_cst.assert_not_called()


# ===========================================================================
# create() paho configuration
# ===========================================================================


class TestCreatePahoConfig:
    async def test_uses_callback_api_v2_without_paho_auto_reconnect(self):
        paho_mock = _make_paho_mock()
        with patch(
            "lghorizon.lghorizon_mqtt_client.mqtt.Client", return_value=paho_mock
        ) as mock_cls:
            with patch(
                "asyncio.AbstractEventLoop.run_in_executor",
                new=AsyncMock(return_value=None),
            ):
                await LGHorizonMqttClient.create(
                    _make_mock_auth(), AsyncMock(), AsyncMock()
                )

        kwargs = mock_cls.call_args.kwargs
        assert kwargs["callback_api_version"] == mqtt.CallbackAPIVersion.VERSION2
        assert kwargs["reconnect_on_failure"] is False


# ===========================================================================
# reconnect loop tests
# ===========================================================================


def _make_reconnecting_client(loop):
    client, auth, *_ = _make_direct_client(loop)
    paho_mock = _make_paho_mock()
    client._mqtt_client = paho_mock
    client._mqtt_broker_url = BROKER_URL_STRIPPED
    return client, auth, paho_mock


@pytest.fixture
def no_backoff():
    with patch("lghorizon.lghorizon_mqtt_client.MAX_RECONNECT_DELAY", 0), patch(
        "lghorizon.lghorizon_mqtt_client.CONNECT_TIMEOUT", 0.05
    ):
        yield


@pytest.mark.usefixtures("no_backoff")
class TestReconnectLoop:
    async def test_manual_connect_in_loop_does_not_cancel_itself(self):
        loop = asyncio.get_running_loop()
        client, auth, paho_mock = _make_reconnecting_client(loop)
        paho_mock.is_connected.side_effect = [False, False, True]

        client._reconnect_task = asyncio.create_task(client._reconnect_loop())
        task = client._reconnect_task
        await asyncio.wait_for(task, timeout=2)

        assert not task.cancelled()
        paho_mock.loop_start.assert_called_once()
        client._message_worker_task.cancel()
        client._publish_worker_task.cancel()

    async def test_uses_fresh_token_for_each_attempt(self):
        loop = asyncio.get_running_loop()
        client, auth, paho_mock = _make_reconnecting_client(loop)
        auth.get_mqtt_token = AsyncMock(side_effect=["token-1", "token-2"])
        paho_mock.connect.side_effect = [OSError("down"), None]
        paho_mock.is_connected.side_effect = lambda: paho_mock.connect.call_count >= 2

        await asyncio.wait_for(client._reconnect_loop(), timeout=2)

        assert [c.args for c in paho_mock.username_pw_set.call_args_list] == [
            (HOUSEHOLD_ID, "token-1"),
            (HOUSEHOLD_ID, "token-2"),
        ]
        client._message_worker_task.cancel()
        client._publish_worker_task.cancel()

    async def test_retries_when_broker_never_accepts_connection(self):
        loop = asyncio.get_running_loop()
        client, auth, paho_mock = _make_reconnecting_client(loop)
        paho_mock.is_connected.side_effect = lambda: paho_mock.connect.call_count >= 3

        await asyncio.wait_for(client._reconnect_loop(), timeout=5)

        assert paho_mock.connect.call_count == 3
        client._message_worker_task.cancel()
        client._publish_worker_task.cancel()

    async def test_token_failure_keeps_retrying(self):
        loop = asyncio.get_running_loop()
        client, auth, paho_mock = _make_reconnecting_client(loop)
        auth.get_mqtt_token = AsyncMock(side_effect=[Exception("boom"), "token"])
        paho_mock.is_connected.side_effect = lambda: paho_mock.connect.call_count >= 1

        await asyncio.wait_for(client._reconnect_loop(), timeout=2)

        assert auth.get_mqtt_token.call_count == 2
        client._message_worker_task.cancel()
        client._publish_worker_task.cancel()

    async def test_joins_previous_paho_thread_before_reconnecting(self):
        loop = asyncio.get_running_loop()
        client, auth, paho_mock = _make_reconnecting_client(loop)
        order: list[str] = []
        paho_mock.loop_stop.side_effect = lambda: order.append("loop_stop")
        paho_mock.connect.side_effect = lambda *a: order.append("connect")
        paho_mock.loop_start.side_effect = lambda: order.append("loop_start")
        paho_mock.is_connected.side_effect = lambda: "loop_start" in order

        await asyncio.wait_for(client._reconnect_loop(), timeout=2)

        assert order == ["loop_stop", "connect", "loop_start"]
        client._message_worker_task.cancel()
        client._publish_worker_task.cancel()

    async def test_clears_task_reference_when_finished(self):
        loop = asyncio.get_running_loop()
        client, auth, paho_mock = _make_reconnecting_client(loop)
        paho_mock.is_connected.return_value = True

        client._start_reconnect_task()
        await asyncio.wait_for(client._reconnect_task, timeout=2)

        assert client._reconnect_task is None

    async def test_disconnect_stops_reconnect_loop(self):
        loop = asyncio.get_running_loop()
        client, auth, paho_mock = _make_reconnecting_client(loop)
        with patch("lghorizon.lghorizon_mqtt_client.MAX_RECONNECT_DELAY", 60):
            client._start_reconnect_task()
            task = client._reconnect_task
            await asyncio.sleep(0)

            await client.disconnect()
            await asyncio.sleep(0)

        assert task.cancelled()
        assert client._reconnect_task is None
        paho_mock.connect.assert_not_called()

    async def test_start_ignored_after_disconnect_requested(self):
        loop = asyncio.get_running_loop()
        client, *_ = _make_reconnecting_client(loop)
        client._disconnect_requested = True

        client._start_reconnect_task()

        assert client._reconnect_task is None
