"""Unit tests for LGHorizonDevice."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, call

from lghorizon.lghorizon_device import LGHorizonDevice
from lghorizon.lghorizon_models import (
    LGHorizonChannel,
    LGHorizonDeviceState,
    LGHorizonRunningState,
    LGHorizonStatusMessage,
    LGHorizonUIStatusMessage,
)
from lghorizon.const import (
    MEDIA_KEY_CHANNEL_DOWN,
    MEDIA_KEY_CHANNEL_UP,
    MEDIA_KEY_ENTER,
    MEDIA_KEY_FAST_FORWARD,
    MEDIA_KEY_PLAY_PAUSE,
    MEDIA_KEY_POWER,
    MEDIA_KEY_RECORD,
    MEDIA_KEY_REWIND,
    MEDIA_KEY_STOP,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DEVICE_JSON = {
    "deviceId": "device-1",
    "hashedCPEId": "hashed-1",
    "platformType": "EOS",
    "settings": {"deviceFriendlyName": "Living Room"},
}


@pytest.fixture
def mqtt_client():
    client = MagicMock()
    client.client_id = "client-123"
    client.publish_message = AsyncMock()
    return client


@pytest.fixture
def processor():
    p = MagicMock()
    p.process_state = AsyncMock()
    p.process_ui_state = AsyncMock()
    return p


@pytest.fixture
def channels(sample_channel_json):
    return {"channel-1": LGHorizonChannel(sample_channel_json)}


@pytest.fixture
def device(mqtt_client, processor, mock_auth, channels):
    return LGHorizonDevice(DEVICE_JSON, mqtt_client, processor, mock_auth, channels)


@pytest.fixture
def running_device(device):
    device._device_state.state = LGHorizonRunningState.ONLINE_RUNNING
    return device


@pytest.fixture
def standby_device(device):
    device._device_state.state = LGHorizonRunningState.ONLINE_STANDBY
    return device


# ---------------------------------------------------------------------------
# Construction & Properties
# ---------------------------------------------------------------------------


def test_device_id(device):
    assert device.device_id == "device-1"


def test_hashed_cpe_id(device):
    assert device.hashed_cpe_id == "hashed-1"


def test_device_friendly_name(device):
    assert device.device_friendly_name == "Living Room"


def test_platform_type(device):
    assert device.platform_type == "EOS"


def test_manufacturer_eos(device):
    assert device.manufacturer == "Arris"


def test_model_eos(device):
    assert device.model == "DCX960"


def test_manufacturer_unknown(mqtt_client, processor, mock_auth, channels):
    device_json = {**DEVICE_JSON, "platformType": "UNKNOWN_PLATFORM"}
    dev = LGHorizonDevice(device_json, mqtt_client, processor, mock_auth, channels)
    assert dev.manufacturer == "unknown"


def test_model_unknown(mqtt_client, processor, mock_auth, channels):
    device_json = {**DEVICE_JSON, "platformType": "UNKNOWN_PLATFORM"}
    dev = LGHorizonDevice(device_json, mqtt_client, processor, mock_auth, channels)
    assert dev.model == "unknown"


def test_is_available_online_running(device):
    device._device_state.state = LGHorizonRunningState.ONLINE_RUNNING
    assert device.is_available is True


def test_is_available_online_standby(device):
    device._device_state.state = LGHorizonRunningState.ONLINE_STANDBY
    assert device.is_available is True


def test_is_available_offline(device):
    device._device_state.state = LGHorizonRunningState.OFFLINE
    assert device.is_available is False


def test_is_available_unknown(device):
    device._device_state.state = LGHorizonRunningState.UNKNOWN
    assert device.is_available is False


def test_initial_device_state(device):
    assert isinstance(device.device_state, LGHorizonDeviceState)
    assert device.device_state.state == LGHorizonRunningState.UNKNOWN


# ---------------------------------------------------------------------------
# set_callback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_callback_stores_callback(device):
    callback = AsyncMock()
    await device.set_callback(callback)
    assert device._change_callback is callback


@pytest.mark.asyncio
async def test_set_callback_calls_register_mqtt(device, mqtt_client, mock_auth):
    callback = AsyncMock()
    await device.set_callback(callback)
    # register_mqtt + _request_settop_box_state + _request_settop_box_recording_capacity
    assert mqtt_client.publish_message.call_count == 3
    # First call: register our own HGO status
    topic, payload_str = mqtt_client.publish_message.call_args_list[0][0]
    assert topic == f"{mock_auth.household_id}/{mqtt_client.client_id}/status"
    payload = json.loads(payload_str)
    assert payload["state"] == LGHorizonRunningState.ONLINE_RUNNING.value


@pytest.mark.asyncio
async def test_set_callback_requests_initial_state(device, mqtt_client, mock_auth):
    """set_callback should request UI state and recording capacity from the box."""
    callback = AsyncMock()
    await device.set_callback(callback)
    calls = mqtt_client.publish_message.call_args_list
    # Second call: CPE.getUiStatus
    state_topic, state_payload_str = calls[1][0]
    assert state_topic == f"{mock_auth.household_id}/{device.device_id}"
    state_payload = json.loads(state_payload_str)
    assert state_payload["type"] == "CPE.getUiStatus"
    # Third call: CPE.capacity
    cap_topic, cap_payload_str = calls[2][0]
    assert cap_topic == f"{mock_auth.household_id}/{device.device_id}"
    cap_payload = json.loads(cap_payload_str)
    assert cap_payload["type"] == "CPE.capacity"


# ---------------------------------------------------------------------------
# handle_status_message
# ---------------------------------------------------------------------------


def _make_status_message(state: str) -> LGHorizonStatusMessage:
    return LGHorizonStatusMessage(
        {"source": "device-1", "state": state, "deviceType": "STB"},
        "some/topic",
    )


@pytest.mark.asyncio
async def test_handle_status_message_processes_state(device, processor):
    msg = _make_status_message("ONLINE_RUNNING")
    await device.handle_status_message(msg)
    processor.process_state.assert_called_once_with(device.device_state, msg)


@pytest.mark.asyncio
async def test_handle_status_message_triggers_callback(device):
    callback = AsyncMock()
    device._change_callback = callback
    msg = _make_status_message("ONLINE_RUNNING")
    await device.handle_status_message(msg)
    callback.assert_called_once_with(device.device_id)


@pytest.mark.asyncio
async def test_handle_status_message_requests_state_when_online_running(
    device, mqtt_client, mock_auth, processor
):
    # Simulate processor updating state to ONLINE_RUNNING
    async def set_running(state, msg):
        state.state = LGHorizonRunningState.ONLINE_RUNNING

    processor.process_state.side_effect = set_running
    msg = _make_status_message("ONLINE_RUNNING")
    await device.handle_status_message(msg)
    # publish_message called for CPE.getUiStatus and CPE.capacity (both via helpers)
    calls_args = [
        json.loads(c[0][1])["type"]
        for c in mqtt_client.publish_message.call_args_list
    ]
    assert "CPE.getUiStatus" in calls_args


@pytest.mark.asyncio
async def test_handle_status_message_no_op_when_same_state(device, processor):
    device._device_state.state = LGHorizonRunningState.ONLINE_RUNNING
    msg = _make_status_message("ONLINE_RUNNING")
    await device.handle_status_message(msg)
    processor.process_state.assert_not_called()


# ---------------------------------------------------------------------------
# handle_ui_status_message
# ---------------------------------------------------------------------------


def _make_ui_status_message(timestamp: int = 1700000000) -> LGHorizonUIStatusMessage:
    return LGHorizonUIStatusMessage(
        {
            "source": "device-1",
            "messageTimeStamp": timestamp,
            "type": "CPE.uiStatus",
            "status": {
                "uiStatus": "mainUI",
                "playerState": {
                    "sourceType": "linear",
                    "speed": 1,
                    "lastSpeedChangeTime": 1700000000000,
                    "relativePosition": 60000,
                    "source": {"channelId": "channel-1", "eventId": "event-1"},
                },
            },
        },
        "some/topic",
    )


@pytest.mark.asyncio
async def test_handle_ui_status_message_calls_process_ui_state(device, processor):
    msg = _make_ui_status_message()
    await device.handle_ui_status_message(msg)
    processor.process_ui_state.assert_called_once_with(device.device_state, msg)


@pytest.mark.asyncio
async def test_handle_ui_status_message_sets_timestamp(device):
    msg = _make_ui_status_message(timestamp=9999)
    await device.handle_ui_status_message(msg)
    assert device.last_ui_message_timestamp == 9.999


@pytest.mark.asyncio
async def test_handle_ui_status_message_triggers_callback(device):
    callback = AsyncMock()
    device._change_callback = callback
    msg = _make_ui_status_message()
    await device.handle_ui_status_message(msg)
    callback.assert_called_once_with(device.device_id)


# ---------------------------------------------------------------------------
# Remote control helpers
# ---------------------------------------------------------------------------


async def _assert_key_sent(device, mqtt_client, mock_auth, coro, expected_key):
    """Helper: call coro and verify the key sent via MQTT."""
    await coro
    mqtt_client.publish_message.assert_called_once()
    topic, payload_str = mqtt_client.publish_message.call_args[0]
    assert topic == f"{mock_auth.household_id}/{device.device_id}"
    payload = json.loads(payload_str)
    assert payload["type"] == "CPE.KeyEvent"
    assert payload["status"]["w3cKey"] == expected_key
    assert payload["status"]["eventType"] == "keyDownUp"


@pytest.mark.asyncio
async def test_turn_on_sends_power_key(standby_device, mqtt_client, mock_auth):
    await _assert_key_sent(
        standby_device, mqtt_client, mock_auth, standby_device.turn_on(), MEDIA_KEY_POWER
    )


@pytest.mark.asyncio
async def test_turn_on_no_op_when_running(running_device, mqtt_client):
    await running_device.turn_on()
    mqtt_client.publish_message.assert_not_called()


@pytest.mark.asyncio
async def test_turn_off_sends_power_key(running_device, mqtt_client, mock_auth):
    await running_device.turn_off()
    mqtt_client.publish_message.assert_called_once()
    payload = json.loads(mqtt_client.publish_message.call_args[0][1])
    assert payload["status"]["w3cKey"] == MEDIA_KEY_POWER


@pytest.mark.asyncio
async def test_turn_off_resets_device_state(running_device):
    # Set some media fields so we can verify reset clears them
    running_device._device_state.channel_id = "ch-99"
    running_device._device_state.speed = 1
    await running_device.turn_off()
    # reset() clears media fields (channel_id, speed) but does not change running state
    assert running_device.device_state.channel_id is None
    assert running_device.device_state.speed is None


@pytest.mark.asyncio
async def test_turn_off_no_op_when_standby(standby_device, mqtt_client):
    await standby_device.turn_off()
    mqtt_client.publish_message.assert_not_called()


@pytest.mark.asyncio
async def test_pause_sends_play_pause(running_device, mqtt_client, mock_auth):
    # paused is computed from speed==0; ensure speed != 0 so not paused
    running_device._device_state.speed = 1
    await _assert_key_sent(
        running_device, mqtt_client, mock_auth, running_device.pause(), MEDIA_KEY_PLAY_PAUSE
    )


@pytest.mark.asyncio
async def test_pause_no_op_when_already_paused(running_device, mqtt_client):
    # paused when speed == 0
    running_device._device_state.speed = 0
    await running_device.pause()
    mqtt_client.publish_message.assert_not_called()


@pytest.mark.asyncio
async def test_play_sends_play_pause(running_device, mqtt_client, mock_auth):
    # paused when speed == 0
    running_device._device_state.speed = 0
    await _assert_key_sent(
        running_device, mqtt_client, mock_auth, running_device.play(), MEDIA_KEY_PLAY_PAUSE
    )


@pytest.mark.asyncio
async def test_play_no_op_when_not_paused(running_device, mqtt_client):
    # speed=1 means not paused
    running_device._device_state.speed = 1
    await running_device.play()
    mqtt_client.publish_message.assert_not_called()


@pytest.mark.asyncio
async def test_stop_sends_stop_key(running_device, mqtt_client, mock_auth):
    await _assert_key_sent(
        running_device, mqtt_client, mock_auth, running_device.stop(), MEDIA_KEY_STOP
    )


@pytest.mark.asyncio
async def test_stop_no_op_when_standby(standby_device, mqtt_client):
    await standby_device.stop()
    mqtt_client.publish_message.assert_not_called()


@pytest.mark.asyncio
async def test_next_channel_sends_channel_up(running_device, mqtt_client, mock_auth):
    await _assert_key_sent(
        running_device, mqtt_client, mock_auth, running_device.next_channel(), MEDIA_KEY_CHANNEL_UP
    )


@pytest.mark.asyncio
async def test_next_channel_no_op_when_standby(standby_device, mqtt_client):
    await standby_device.next_channel()
    mqtt_client.publish_message.assert_not_called()


@pytest.mark.asyncio
async def test_previous_channel_sends_channel_down(running_device, mqtt_client, mock_auth):
    await _assert_key_sent(
        running_device,
        mqtt_client,
        mock_auth,
        running_device.previous_channel(),
        MEDIA_KEY_CHANNEL_DOWN,
    )


@pytest.mark.asyncio
async def test_previous_channel_no_op_when_standby(standby_device, mqtt_client):
    await standby_device.previous_channel()
    mqtt_client.publish_message.assert_not_called()


@pytest.mark.asyncio
async def test_press_enter_sends_enter_key(running_device, mqtt_client, mock_auth):
    await _assert_key_sent(
        running_device, mqtt_client, mock_auth, running_device.press_enter(), MEDIA_KEY_ENTER
    )


@pytest.mark.asyncio
async def test_press_enter_no_op_when_standby(standby_device, mqtt_client):
    await standby_device.press_enter()
    mqtt_client.publish_message.assert_not_called()


@pytest.mark.asyncio
async def test_rewind_sends_rewind_key(running_device, mqtt_client, mock_auth):
    await _assert_key_sent(
        running_device, mqtt_client, mock_auth, running_device.rewind(), MEDIA_KEY_REWIND
    )


@pytest.mark.asyncio
async def test_rewind_no_op_when_standby(standby_device, mqtt_client):
    await standby_device.rewind()
    mqtt_client.publish_message.assert_not_called()


@pytest.mark.asyncio
async def test_fast_forward_sends_fast_forward_key(running_device, mqtt_client, mock_auth):
    await _assert_key_sent(
        running_device,
        mqtt_client,
        mock_auth,
        running_device.fast_forward(),
        MEDIA_KEY_FAST_FORWARD,
    )


@pytest.mark.asyncio
async def test_fast_forward_no_op_when_standby(standby_device, mqtt_client):
    await standby_device.fast_forward()
    mqtt_client.publish_message.assert_not_called()


@pytest.mark.asyncio
async def test_record_sends_record_key(running_device, mqtt_client, mock_auth):
    await _assert_key_sent(
        running_device, mqtt_client, mock_auth, running_device.record(), MEDIA_KEY_RECORD
    )


@pytest.mark.asyncio
async def test_record_no_op_when_standby(standby_device, mqtt_client):
    await standby_device.record()
    mqtt_client.publish_message.assert_not_called()


# ---------------------------------------------------------------------------
# send_key_to_box
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_key_to_box_payload(device, mqtt_client, mock_auth):
    await device.send_key_to_box("SomeKey")
    mqtt_client.publish_message.assert_called_once()
    topic, payload_str = mqtt_client.publish_message.call_args[0]
    assert topic == f"{mock_auth.household_id}/{device.device_id}"
    payload = json.loads(payload_str)
    assert payload["type"] == "CPE.KeyEvent"
    assert payload["runtimeType"] == "key"
    assert payload["status"]["w3cKey"] == "SomeKey"
    assert payload["status"]["eventType"] == "keyDownUp"
    assert payload["source"] == device.device_id.lower()


# ---------------------------------------------------------------------------
# set_channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_channel_publishes_correct_payload(device, mqtt_client, mock_auth):
    await device.set_channel("NPO 1")
    mqtt_client.publish_message.assert_called_once()
    topic, payload_str = mqtt_client.publish_message.call_args[0]
    assert topic == f"{mock_auth.household_id}/{device.device_id}"
    payload = json.loads(payload_str)
    assert payload["type"] == "CPE.pushToTV"
    assert payload["status"]["sourceType"] == "linear"
    assert payload["status"]["source"]["channelId"] == "channel-1"


@pytest.mark.asyncio
async def test_set_channel_raises_for_unknown_channel(device):
    with pytest.raises(ValueError, match="not found"):
        await device.set_channel("Nonexistent Channel")


# ---------------------------------------------------------------------------
# play_recording
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_play_recording_publishes_ndvr_payload(device, mqtt_client, mock_auth):
    await device.play_recording("rec-42")
    mqtt_client.publish_message.assert_called_once()
    topic, payload_str = mqtt_client.publish_message.call_args[0]
    assert topic == f"{mock_auth.household_id}/{device.device_id}"
    payload = json.loads(payload_str)
    assert payload["type"] == "CPE.pushToTV"
    assert payload["status"]["sourceType"] == "nDVR"
    assert payload["status"]["source"]["recordingId"] == "rec-42"
