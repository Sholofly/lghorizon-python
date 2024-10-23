from datetime import datetime
from typing import Any, Callable, Dict, List
import paho.mqtt.client as mqtt
import requests
from .const import (
    BOX_PLAY_STATE_BUFFER,
    BOX_PLAY_STATE_CHANNEL,
    BOX_PLAY_STATE_DVR,
    BOX_PLAY_STATE_REPLAY,
    BOX_PLAY_STATE_APP,
    BOX_PLAY_STATE_VOD,
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
    RECORDING_TYPE_SEASON,
    RECORDING_TYPE_SHOW,
)

import json
from .helpers import make_id
import logging

_logger = logging.getLogger(__name__)


class LGHorizonAuth:
    householdId: str
    accessToken: str
    refreshToken: str
    refreshTokenExpiry: datetime
    username: str
    mqttToken: str = None
    accessToken: str = None

    def __init__(self):
        """Initialize a session."""
        pass

    def fill(self, auth_json) -> None:
        self.householdId = auth_json["householdId"]
        self.accessToken = auth_json["accessToken"]
        self.refreshToken = auth_json["refreshToken"]
        self.username = auth_json["username"]
        try:
            self.refreshTokenExpiry = datetime.fromtimestamp(
                auth_json["refreshTokenExpiry"]
            )
        except ValueError:
            # VM uses milliseconds for the expiry time; if the year is too high to be valid, it assumes it's milliseconds and divides it
            self.refreshTokenExpiry = datetime.fromtimestamp(
                auth_json["refreshTokenExpiry"] // 1000
            )

    def is_expired(self) -> bool:
        return self.refreshTokenExpiry


class LGHorizonPlayingInfo:
    """Represent current state of a box."""

    channel_id: str = None
    title: str = None
    image: str = None
    source_type: str = None
    paused: bool = False
    channel_title: str = None
    duration: float = None
    position: float = None
    last_position_update: datetime = None

    def __init__(self):
        """Initialize the playing info."""
        pass

    def set_paused(self, paused: bool):
        """Set pause state."""
        self.paused = paused

    def set_channel(self, channel_id):
        """Set channel."""
        self.channel_id = channel_id

    def set_title(self, title):
        """Set title."""
        self.title = title

    def set_channel_title(self, title):
        """Set channel title."""
        self.channel_title = title

    def set_image(self, image):
        """Set image."""
        self.image = image

    def set_source_type(self, source_type):
        """Set source type."""
        self.source_type = source_type

    def set_duration(self, duration: float):
        """Set duration."""
        self.duration = duration

    def set_position(self, position: float):
        """Set position."""
        self.position = position

    def set_last_position_update(self, last_position_update: datetime):
        """Set last position update."""
        self.last_position_update = last_position_update

    def reset_progress(self):
        self.last_position_update = None
        self.duration = None
        self.position = None

    def reset(self):
        self.channel_id = None
        self.title = None
        self.image = None
        self.source_type = None
        self.paused = False
        self.channel_title = None
        self.reset_progress()


class LGHorizonChannel:
    """Represent a channel."""

    id: str
    title: str
    stream_image: str
    logo_image: str
    channel_number: str

    def __init__(self, channel_json):
        """Initialize a channel."""
        self.id = channel_json["id"]
        self.title = channel_json["name"]
        self.stream_image = self.get_stream_image(channel_json)
        if "logo" in channel_json and "focused" in channel_json["logo"]:
            self.logo_image = channel_json["logo"]["focused"]
        else:
            self.logo_image = ""
        self.channel_number = channel_json["logicalChannelNumber"]

    def get_stream_image(self, channel_json) -> str:
        image_stream = channel_json["imageStream"]
        if "full" in image_stream:
            return image_stream["full"]
        if "small" in image_stream:
            return image_stream["small"]
        if "logo" in channel_json and "focused" in channel_json["logo"]:
            return channel_json["logo"]["focused"]
        return ""


class LGHorizonReplayEvent:
    episodeNumber: int = None
    channelId: str = None
    eventId: str = None
    seasonNumber: int = None
    title: str = None
    episodeName: str = None

    def __init__(self, raw_json: str):
        self.channelId = raw_json["channelId"]
        self.eventId = raw_json["eventId"]
        self.title = raw_json["title"]
        if "episodeName" in raw_json:
            self.episodeName = raw_json["episodeName"]
        if "episodeNumber" in raw_json:
            self.episodeNumber = raw_json["episodeNumber"]
        if "seasonNumber" in raw_json:
            self.seasonNumber = raw_json["seasonNumber"]


class LGHorizonBaseRecording:
    id: str = None
    title: str = None
    image: str = None
    type: str = None
    channelId: str = None

    def __init__(
        self, id: str, title: str, image: str, channelId: str, type: str
    ) -> None:
        self.id = id
        self.title = title
        self.image = image
        self.channelId = channelId
        self.type = type


class LGHorizonRecordingSingle(LGHorizonBaseRecording):
    """Represents a single recording."""

    seasonNumber: int = None
    episodeNumber: int = None

    def __init__(self, recording_json):
        """Init the single recording."""
        poster_url = None
        if "poster" in recording_json and "url" in recording_json["poster"]:
            poster_url = recording_json["poster"]["url"]
        LGHorizonBaseRecording.__init__(
            self,
            recording_json["id"],
            recording_json["title"],
            poster_url,
            recording_json["channelId"],
            recording_json["type"],
        )
        if "seasonNumber" in recording_json:
            self.seasonNumber = recording_json["seasonNumber"]
        if "episodeNumber" in recording_json:
            self.episodeNumber = recording_json["episodeNumber"]


class LGHorizonRecordingEpisode:
    """Represents a single recording."""

    episodeId: str = None
    episodeTitle: str = None
    seasonNumber: int = None
    episodeNumber: int = None
    showTitle: str = None
    recordingState: str = None
    image: str = None

    def __init__(self, recording_json):
        """Init the single recording."""
        self.episodeId = recording_json["episodeId"]
        self.episodeTitle = recording_json["episodeTitle"]
        self.showTitle = recording_json["showTitle"]
        self.recordingState = recording_json["recordingState"]
        if "seasonNumber" in recording_json:
            self.seasonNumber = recording_json["seasonNumber"]
        if "episodeNumber" in recording_json:
            self.episodeNumber = recording_json["episodeNumber"]
        if "poster" in recording_json and "url" in recording_json["poster"]:
            self.image = recording_json["poster"]["url"]


class LGHorizonRecordingShow:
    """Represents a single recording."""

    episodeId: str = None
    showTitle: str = None
    seasonNumber: int = None
    episodeNumber: int = None
    recordingState: str = None
    image: str = None

    def __init__(self, recording_json):
        """Init the single recording."""
        self.episodeId = recording_json["episodeId"]
        self.showTitle = recording_json["showTitle"]
        self.recordingState = recording_json["recordingState"]
        if "seasonNumber" in recording_json:
            self.seasonNumber = recording_json["seasonNumber"]
        if "episodeNumber" in recording_json:
            self.episodeNumber = recording_json["episodeNumber"]
        if "poster" in recording_json and "url" in recording_json["poster"]:
            self.image = recording_json["poster"]["url"]


class LGHorizonRecordingListSeasonShow(LGHorizonBaseRecording):
    showId: str = None

    def __init__(self, recording_season_json):
        """Init the single recording."""

        LGHorizonBaseRecording.__init__(
            self,
            recording_season_json["id"],
            recording_season_json["title"],
            recording_season_json["poster"]["url"],
            recording_season_json["channelId"],
            recording_season_json["type"],
        )
        if self.type == RECORDING_TYPE_SEASON:
            self.showId = recording_season_json["showId"]
        else:
            self.showId = recording_season_json["id"]


class LGHorizonVod:
    title: str = None
    image: str = None
    duration: float = None

    def __init__(self, vod_json) -> None:
        self.title = vod_json["title"]
        self.duration = vod_json["duration"]


class LGHorizonApp:
    title: str = None
    image: str = None

    def __init__(self, app_state_json: str) -> None:
        self.title = app_state_json["appName"]
        self.image = app_state_json["logoPath"]
        if not self.image.startswith("http:"):
            self.image = "https:" + self.image


class LGHorizonMqttClient:
    _brokerUrl: str = None
    _mqtt_client: mqtt.Client
    _auth: LGHorizonAuth
    clientId: str = None
    _on_connected_callback: Callable = None
    _on_message_callback: Callable[[str, str], None] = None

    @property
    def is_connected(self):
        return self._mqtt_client.is_connected

    def __init__(
        self,
        auth: LGHorizonAuth,
        mqtt_broker_url: str,
        on_connected_callback: Callable = None,
        on_message_callback: Callable[[str], None] = None,
    ):
        self._auth = auth
        self._brokerUrl = mqtt_broker_url.replace("wss://", "").replace(":443/mqtt", "")
        self.clientId = make_id()
        self._mqtt_client = mqtt.Client(self.clientId, transport="websockets")

        self._mqtt_client.ws_set_options(
            headers={"Sec-WebSocket-Protocol": "mqtt, mqttv3.1, mqttv3.11"}
        )
        self._mqtt_client.username_pw_set(self._auth.householdId, self._auth.mqttToken)
        self._mqtt_client.tls_set()
        self._mqtt_client.enable_logger(_logger)
        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._on_connected_callback = on_connected_callback
        self._on_message_callback = on_message_callback

    def _on_mqtt_connect(self, client, userdata, flags, resultCode):
        if resultCode == 0:
            self._mqtt_client.on_message = self._on_client_message
            self._mqtt_client.subscribe(self._auth.householdId)
            self._mqtt_client.subscribe(self._auth.householdId + "/#")
            self._mqtt_client.subscribe(self._auth.householdId + "/" + self.clientId)
            self._mqtt_client.subscribe(self._auth.householdId + "/+/status")
            self._mqtt_client.subscribe(self._auth.householdId + "/+/networkRecordings")
            self._mqtt_client.subscribe(
                self._auth.householdId + "/+/networkRecordings/capacity"
            )
            self._mqtt_client.subscribe(self._auth.householdId + "/+/localRecordings")
            self._mqtt_client.subscribe(
                self._auth.householdId + "/+/localRecordings/capacity"
            )
            self._mqtt_client.subscribe(self._auth.householdId + "/watchlistService")
            self._mqtt_client.subscribe(self._auth.householdId + "/purchaseService")
            self._mqtt_client.subscribe(
                self._auth.householdId + "/personalizationService"
            )
            self._mqtt_client.subscribe(self._auth.householdId + "/recordingStatus")
            self._mqtt_client.subscribe(
                self._auth.householdId + "/recordingStatus/lastUserAction"
            )
            if self._on_connected_callback:
                self._on_connected_callback()
        elif resultCode == 5:
            self._mqtt_client.username_pw_set(
                self._auth.householdId, self._auth.mqttToken
            )
            self.connect()
        else:
            _logger.error(
                f"Cannot connect to MQTT server with resultCode: {resultCode}"
            )

    def connect(self) -> None:
        self._mqtt_client.connect(self._brokerUrl, 443)
        self._mqtt_client.loop_start()

    def _on_client_message(self, client, userdata, message):
        """Handle messages received by mqtt client."""
        _logger.debug(f"Received MQTT message. Topic: {message.topic}")
        jsonPayload = json.loads(message.payload)
        _logger.debug(f"Message: {jsonPayload}")
        if self._on_message_callback:
            self._on_message_callback(jsonPayload, message.topic)

    def publish_message(self, topic: str, json_payload: str) -> None:
        self._mqtt_client.publish(topic, json_payload, qos=2)

    def disconnect(self) -> None:
        if self._mqtt_client.is_connected:
            self._mqtt_client.disconnect()


class LGHorizonBox:
    deviceId: str = None
    hashedCPEId: str = None
    deviceFriendlyName: str = None
    state: str = None
    playing_info: LGHorizonPlayingInfo = None
    manufacturer: str = None
    model: str = None
    recording_capacity: int = None

    _mqtt_client: LGHorizonMqttClient
    _change_callback: Callable = None
    _auth: LGHorizonAuth = None
    _channels: Dict[str, LGHorizonChannel] = None
    _message_stamp = None

    def __init__(
        self,
        box_json: str,
        platform_type: Dict[str, str],
        mqtt_client: LGHorizonMqttClient,
        auth: LGHorizonAuth,
        channels: Dict[str, LGHorizonChannel],
    ):
        self.deviceId = box_json["deviceId"]
        self.hashedCPEId = box_json["hashedCPEId"]
        self.deviceFriendlyName = box_json["settings"]["deviceFriendlyName"]
        self._mqtt_client = mqtt_client
        self._auth = auth
        self._channels = channels
        self.playing_info = LGHorizonPlayingInfo()
        if platform_type:
            self.manufacturer = platform_type["manufacturer"]
            self.model = platform_type["model"]

    def register_mqtt(self) -> None:
        if not self._mqtt_client.is_connected:
            raise Exception("MQTT client not connected.")
        topic = f"{self._auth.householdId}/{self._mqtt_client.clientId}/status"
        payload = {
            "source": self._mqtt_client.clientId,
            "state": ONLINE_RUNNING,
            "deviceType": "HGO",
        }
        self._mqtt_client.publish_message(topic, json.dumps(payload))

    def set_callback(self, change_callback: Callable) -> None:
        self._change_callback = change_callback

    def update_state(self, payload):
        """Register a new settop box."""
        state = payload["state"]
        if self.state == state:
            return
        self.state = state
        if state == ONLINE_STANDBY:
            self.playing_info.reset()
            if self._change_callback:
                self._change_callback(self.deviceId)
        else:
            self._request_settop_box_state()
        self._request_settop_box_recording_capacity()

    def update_recording_capacity(self, payload) -> None:
        if not "CPE.capacity" in payload or not "used" in payload:
            return
        self.recording_capacity = payload["used"]

    def update_with_replay_event(
        self, source_type: str, event: LGHorizonReplayEvent, channel: LGHorizonChannel
    ) -> None:
        self.playing_info.set_source_type(source_type)
        self.playing_info.set_channel(channel.id)
        self.playing_info.set_channel_title(channel.title)
        title = event.title
        if event.episodeName:
            title += f": {event.episodeName}"
        self.playing_info.set_title(title)
        self.playing_info.set_image(channel.stream_image)
        self.playing_info.reset_progress()
        self._trigger_callback()

    def update_with_recording(
        self,
        source_type: str,
        recording: LGHorizonRecordingSingle,
        channel: LGHorizonChannel,
        start: float,
        end: float,
        last_speed_change: float,
        relative_position: float,
    ) -> None:
        self.playing_info.set_source_type(source_type)
        self.playing_info.set_channel(channel.id)
        self.playing_info.set_channel_title(channel.title)
        self.playing_info.set_title(f"{recording.title}")
        self.playing_info.set_image(recording.image)
        start_dt = datetime.fromtimestamp(start / 1000.0)
        end_dt = datetime.fromtimestamp(end / 1000.0)
        duration = (end_dt - start_dt).total_seconds()
        self.playing_info.set_duration(duration)
        self.playing_info.set_position(relative_position / 1000.0)
        last_update_dt = datetime.fromtimestamp(last_speed_change / 1000.0)
        self.playing_info.set_last_position_update(last_update_dt)
        self._trigger_callback()

    def update_with_vod(
        self,
        source_type: str,
        vod: LGHorizonVod,
        last_speed_change: float,
        relative_position: float,
    ) -> None:
        self.playing_info.set_source_type(source_type)
        self.playing_info.set_channel(None)
        self.playing_info.set_channel_title(None)
        self.playing_info.set_title(vod.title)
        self.playing_info.set_image(None)
        self.playing_info.set_duration(vod.duration)
        self.playing_info.set_position(relative_position / 1000.0)
        last_update_dt = datetime.fromtimestamp(last_speed_change / 1000.0)
        self.playing_info.set_last_position_update(last_update_dt)
        self._trigger_callback()

    def update_with_app(self, source_type: str, app: LGHorizonApp) -> None:
        self.playing_info.set_source_type(source_type)
        self.playing_info.set_channel(None)
        self.playing_info.set_channel_title(app.title)
        self.playing_info.set_title(app.title)
        self.playing_info.set_image(app.image)
        self.playing_info.reset_progress()
        self._trigger_callback()

    def _trigger_callback(self):
        if self._change_callback:
            _logger.debug(f"Callback called from box {self.deviceId}")
            self._change_callback(self.deviceId)

    def turn_on(self) -> None:
        """Turn the settop box on."""

        if self.state == ONLINE_STANDBY:
            self.send_key_to_box(MEDIA_KEY_POWER)

    def turn_off(self) -> None:
        """Turn the settop box off."""
        if self.state == ONLINE_RUNNING:
            self.send_key_to_box(MEDIA_KEY_POWER)
            self.playing_info.reset()

    def pause(self) -> None:
        """Pause the given settopbox."""
        if self.state == ONLINE_RUNNING and not self.playing_info.paused:
            self.send_key_to_box(MEDIA_KEY_PLAY_PAUSE)

    def play(self) -> None:
        """Resume the settopbox."""
        if self.state == ONLINE_RUNNING and self.playing_info.paused:
            self.send_key_to_box(MEDIA_KEY_PLAY_PAUSE)

    def stop(self) -> None:
        """Stop the settopbox."""
        if self.state == ONLINE_RUNNING:
            self.send_key_to_box(MEDIA_KEY_STOP)

    def next_channel(self):
        """Select the next channel for given settop box."""
        if self.state == ONLINE_RUNNING:
            self.send_key_to_box(MEDIA_KEY_CHANNEL_UP)

    def previous_channel(self) -> None:
        """Select the previous channel for given settop box."""
        if self.state == ONLINE_RUNNING:
            self.send_key_to_box(MEDIA_KEY_CHANNEL_DOWN)

    def press_enter(self) -> None:
        """Press enter on the settop box."""
        if self.state == ONLINE_RUNNING:
            self.send_key_to_box(MEDIA_KEY_ENTER)

    def rewind(self) -> None:
        """Rewind the settop box."""
        if self.state == ONLINE_RUNNING:
            self.send_key_to_box(MEDIA_KEY_REWIND)

    def fast_forward(self) -> None:
        """Fast forward the settop box."""
        if self.state == ONLINE_RUNNING:
            self.send_key_to_box(MEDIA_KEY_FAST_FORWARD)

    def record(self):
        """Record on the settop box."""
        if self.state == ONLINE_RUNNING:
            self.send_key_to_box(MEDIA_KEY_RECORD)

    def is_available(self) -> bool:
        """Return the availability of the settop box."""
        return self.state == ONLINE_RUNNING or self.state == ONLINE_STANDBY

    def set_channel(self, source: str) -> None:
        """Change te channel from the settopbox."""
        channel = [src for src in self._channels.values() if src.title == source][0]
        payload = (
            '{"id":"'
            + make_id(8)
            + '","type":"CPE.pushToTV","source":{"clientId":"'
            + self._mqtt_client.clientId
            + '","friendlyDeviceName":"Home Assistant"},'
            + '"status":{"sourceType":"linear","source":{"channelId":"'
            + channel.id
            + '"},"relativePosition":0,"speed":1}}'
        )

        self._mqtt_client.publish_message(
            f"{self._auth.householdId}/{self.deviceId}", payload
        )

    def play_recording(self, recordingId):
        """Play recording."""
        payload = (
            '{"id":"'
            + make_id(8)
            + '","type":"CPE.pushToTV","source":{"clientId":"'
            + self._mqtt_client.clientId
            + '","friendlyDeviceName":"Home Assistant"},'
            + '"status":{"sourceType":"nDVR","source":{"recordingId":"'
            + recordingId
            + '"},"relativePosition":0}}'
        )
        self._mqtt_client.publish_message(
            f"{self._auth.householdId}/{self.deviceId}", payload
        )

    def send_key_to_box(self, key: str) -> None:
        """Send emulated (remote) key press to settopbox."""
        payload = (
            '{"type":"CPE.KeyEvent","status":{"w3cKey":"'
            + key
            + '","eventType":"keyDownUp"}}'
        )
        self._mqtt_client.publish_message(
            f"{self._auth.householdId}/{self.deviceId}", payload
        )

    def _set_unknown_channel_info(self) -> None:
        """Set unknown channel info."""
        _logger.warning("Couldn't set channel. Channel info set to unknown...")
        self.playing_info.set_source_type(BOX_PLAY_STATE_CHANNEL)
        self.playing_info.set_channel(None)
        self.playing_info.set_title("No information available")
        self.playing_info.set_image(None)
        self.playing_info.set_paused(False)

    def _request_settop_box_state(self) -> None:
        """Send mqtt message to receive state from settop box."""
        topic = f"{self._auth.householdId}/{self.deviceId}"
        payload = {
            "id": make_id(8),
            "type": "CPE.getUiStatus",
            "source": self._mqtt_client.clientId,
        }
        self._mqtt_client.publish_message(topic, json.dumps(payload))

    def _request_settop_box_recording_capacity(self) -> None:
        """Send mqtt message to receive state from settop box."""
        topic = f"{self._auth.householdId}/{self.deviceId}"
        payload = {
            "id": make_id(8),
            "type": "CPE.capacity",
            "source": self._mqtt_client.clientId,
        }
        self._mqtt_client.publish_message(topic, json.dumps(payload))


class LGHorizonProfile:
    profile_id: str = None
    name: str = None
    favorite_channels: [] = None

    def __init__(self, json_payload):
        self.profile_id = json_payload["profileId"]
        self.name = json_payload["name"]
        self.favorite_channels = json_payload["favoriteChannels"]


class LGHorizonCustomer:
    customerId: str = None
    hashedCustomerId: str = None
    countryId: str = None
    cityId: int = 0
    settop_boxes: [] = None
    profiles: Dict[str, LGHorizonProfile] = {}

    def __init__(self, json_payload):
        self.customerId = json_payload["customerId"]
        self.hashedCustomerId = json_payload["hashedCustomerId"]
        self.countryId = json_payload["countryId"]
        self.cityId = json_payload["cityId"]
        if "assignedDevices" in json_payload:
            self.settop_boxes = json_payload["assignedDevices"]
        if "profiles" in json_payload:
            for profile in json_payload["profiles"]:
                self.profiles[profile["profileId"]] = LGHorizonProfile(profile)
