"""Models for LGHorizon API."""

# pylint: disable=broad-exception-caught
# pylint: disable=broad-exception-raised
from datetime import datetime
from typing import Callable, Dict
import json
import logging
import paho.mqtt.client as mqtt

from .const import (
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
    RECORDING_TYPE_SEASON,
)

from .helpers import make_id

_logger = logging.getLogger(__name__)


class LGHorizonAuth:
    """Class to hold LGHorizon authentication."""

    household_id: str
    access_token: str
    refresh_token: str
    refresh_token_expiry: datetime
    username: str
    mqtt_token: str = None
    access_token: str = None

    def __init__(self):
        """Initialize a session."""

    def fill(self, auth_json) -> None:
        """Fill the object."""
        self.household_id = auth_json["householdId"]
        self.access_token = auth_json["accessToken"]
        self.refresh_token = auth_json["refreshToken"]
        self.username = auth_json["username"]
        try:
            self.refresh_token_expiry = datetime.fromtimestamp(
                auth_json["refreshTokenExpiry"]
            )
        except ValueError:
            # VM uses milliseconds for the expiry time.
            # If the year is too high to be valid, it assumes it's milliseconds and divides it
            self.refresh_token_expiry = datetime.fromtimestamp(
                auth_json["refreshTokenExpiry"] // 1000
            )

    def is_expired(self) -> bool:
        """Check if refresh token is expired."""
        return self.refresh_token_expiry


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
        """Reset the progress."""
        self.last_position_update = None
        self.duration = None
        self.position = None

    def reset(self):
        """Reset the channel"""
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
        """Returns the stream image."""
        image_stream = channel_json["imageStream"]
        if "full" in image_stream:
            return image_stream["full"]
        if "small" in image_stream:
            return image_stream["small"]
        if "logo" in channel_json and "focused" in channel_json["logo"]:
            return channel_json["logo"]["focused"]
        return ""


class LGHorizonReplayEvent:
    """LGhorizon replay event."""

    episode_number: int = None
    channel_id: str = None
    event_id: str = None
    season_number: int = None
    title: str = None
    episode_name: str = None

    def __init__(self, raw_json: str):
        self.channel_id = raw_json["channelId"]
        self.event_id = raw_json["eventId"]
        self.title = raw_json["title"]
        if "episodeName" in raw_json:
            self.episode_name = raw_json["episodeName"]
        if "episodeNumber" in raw_json:
            self.episode_number = raw_json["episodeNumber"]
        if "seasonNumber" in raw_json:
            self.season_number = raw_json["seasonNumber"]


class LGHorizonBaseRecording:
    """LgHorizon base recording."""

    recording_id: str = None
    title: str = None
    image: str = None
    recording_type: str = None
    channel_id: str = None

    def __init__(
        self,
        recording_id: str,
        title: str,
        image: str,
        channel_id: str,
        recording_type: str,
    ) -> None:
        self.recording_id = recording_id
        self.title = title
        self.image = image
        self.channel_id = channel_id
        self.recording_type = recording_type


class LGHorizonRecordingSingle(LGHorizonBaseRecording):
    """Represents a single recording."""

    season_number: int = None
    episode_number: int = None

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
            self.season_number = recording_json["seasonNumber"]
        if "episodeNumber" in recording_json:
            self.episode_number = recording_json["episodeNumber"]


class LGHorizonRecordingEpisode:
    """Represents a single recording."""

    episode_id: str = None
    episode_title: str = None
    season_number: int = None
    episode_number: int = None
    show_title: str = None
    recording_state: str = None
    image: str = None

    def __init__(self, recording_json):
        """Init the single recording."""
        self.episode_id = recording_json["episodeId"]
        self.episode_title = recording_json["episodeTitle"]
        self.show_title = recording_json["showTitle"]
        self.recording_state = recording_json["recordingState"]
        if "seasonNumber" in recording_json:
            self.season_number = recording_json["seasonNumber"]
        if "episodeNumber" in recording_json:
            self.episode_number = recording_json["episodeNumber"]
        if "poster" in recording_json and "url" in recording_json["poster"]:
            self.image = recording_json["poster"]["url"]


class LGHorizonRecordingShow:
    """Represents a single recording."""

    episode_id: str = None
    show_title: str = None
    season_number: int = None
    episode_number: int = None
    recording_state: str = None
    image: str = None

    def __init__(self, recording_json):
        """Init the single recording."""
        self.episode_id = recording_json["episodeId"]
        self.show_title = recording_json["showTitle"]
        self.recording_state = recording_json["recordingState"]
        if "seasonNumber" in recording_json:
            self.season_number = recording_json["seasonNumber"]
        if "episodeNumber" in recording_json:
            self.episode_number = recording_json["episodeNumber"]
        if "poster" in recording_json and "url" in recording_json["poster"]:
            self.image = recording_json["poster"]["url"]


class LGHorizonRecordingListSeasonShow(LGHorizonBaseRecording):
    """LGHorizon Season show list."""

    show_id: str = None

    def __init__(self, recording_season_json):
        """Init the single recording."""

        poster_url = None
        if (
            "poster" in recording_season_json
            and "url" in recording_season_json["poster"]
        ):
            poster_url = recording_season_json["poster"]["url"]
        LGHorizonBaseRecording.__init__(
            self,
            recording_season_json["id"],
            recording_season_json["title"],
            poster_url,
            recording_season_json["channelId"],
            recording_season_json["type"],
        )
        if self.recording_type == RECORDING_TYPE_SEASON:
            self.show_id = recording_season_json["showId"]
        else:
            self.show_id = recording_season_json["id"]


class LGHorizonVod:
    """LGHorizon video on demand."""

    title: str = None
    image: str = None
    duration: float = None

    def __init__(self, vod_json) -> None:
        self.title = vod_json["title"]
        self.duration = vod_json["duration"]


class LGHorizonApp:
    """LGHorizon App."""

    title: str = None
    image: str = None

    def __init__(self, app_state_json: str) -> None:
        self.title = app_state_json["appName"]
        self.image = app_state_json["logoPath"]
        if not self.image.startswith("http:"):
            self.image = "https:" + self.image


class LGHorizonMqttClient:
    """LGHorizon MQTT client."""

    _broker_url: str = None
    _mqtt_client: mqtt.Client
    _auth: LGHorizonAuth
    client_id: str = None
    _on_connected_callback: Callable = None
    _on_message_callback: Callable[[str, str], None] = None

    @property
    def is_connected(self):
        """Is client connected."""
        return self._mqtt_client.is_connected

    def __init__(
        self,
        auth: LGHorizonAuth,
        mqtt_broker_url: str,
        on_connected_callback: Callable = None,
        on_message_callback: Callable[[str], None] = None,
    ):
        self._auth = auth
        self._broker_url = mqtt_broker_url.replace("wss://", "").replace(
            ":443/mqtt", ""
        )
        self.client_id = make_id()
        self._mqtt_client = mqtt.Client(
            client_id=self.client_id,
            transport="websockets",
        )

        self._mqtt_client.ws_set_options(
            headers={"Sec-WebSocket-Protocol": "mqtt, mqttv3.1, mqttv3.11"}
        )
        self._mqtt_client.username_pw_set(
            self._auth.household_id, self._auth.mqtt_token
        )
        self._mqtt_client.tls_set()
        self._mqtt_client.enable_logger(_logger)
        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._on_connected_callback = on_connected_callback
        self._on_message_callback = on_message_callback

    def _on_mqtt_connect(self, client, userdata, flags, result_code):  # pylint: disable=unused-argument
        if result_code == 0:
            self._mqtt_client.on_message = self._on_client_message
            self._mqtt_client.subscribe(self._auth.household_id)
            self._mqtt_client.subscribe(self._auth.household_id + "/#")
            self._mqtt_client.subscribe(self._auth.household_id + "/" + self.client_id)
            self._mqtt_client.subscribe(self._auth.household_id + "/+/status")
            self._mqtt_client.subscribe(
                self._auth.household_id + "/+/networkRecordings"
            )
            self._mqtt_client.subscribe(
                self._auth.household_id + "/+/networkRecordings/capacity"
            )
            self._mqtt_client.subscribe(self._auth.household_id + "/+/localRecordings")
            self._mqtt_client.subscribe(
                self._auth.household_id + "/+/localRecordings/capacity"
            )
            self._mqtt_client.subscribe(self._auth.household_id + "/watchlistService")
            self._mqtt_client.subscribe(self._auth.household_id + "/purchaseService")
            self._mqtt_client.subscribe(
                self._auth.household_id + "/personalizationService"
            )
            self._mqtt_client.subscribe(self._auth.household_id + "/recordingStatus")
            self._mqtt_client.subscribe(
                self._auth.household_id + "/recordingStatus/lastUserAction"
            )
            if self._on_connected_callback:
                self._on_connected_callback()
        elif result_code == 5:
            self._mqtt_client.username_pw_set(
                self._auth.household_id, self._auth.mqtt_token
            )
            self.connect()
        else:
            _logger.error(
                "Cannot connect to MQTT server with resultCode: %s", result_code
            )

    def connect(self) -> None:
        """Connect the client."""
        self._mqtt_client.connect(self._broker_url, 443)
        self._mqtt_client.loop_start()

    def _on_client_message(self, client, userdata, message):  # pylint: disable=unused-argument
        """Handle messages received by mqtt client."""
        _logger.debug("Received MQTT message. Topic: %s", message.topic)
        json_payload = json.loads(message.payload)
        _logger.debug("Message: %s", json_payload)
        if self._on_message_callback:
            self._on_message_callback(json_payload, message.topic)

    def publish_message(self, topic: str, json_payload: str) -> None:
        """Publish a MQTT message."""
        self._mqtt_client.publish(topic, json_payload, qos=2)

    def disconnect(self) -> None:
        """Disconnect the client."""
        if self._mqtt_client.is_connected():
            self._mqtt_client.disconnect()


class LGHorizonBox:
    """The LGHorizon box."""

    device_id: str = None
    hashed_cpe_id: str = None
    device_friendly_name: str = None
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
        self.device_id = box_json["deviceId"]
        self.hashed_cpe_id = box_json["hashedCPEId"]
        self.device_friendly_name = box_json["settings"]["deviceFriendlyName"]
        self._mqtt_client = mqtt_client
        self._auth = auth
        self._channels = channels
        self.playing_info = LGHorizonPlayingInfo()
        if platform_type:
            self.manufacturer = platform_type["manufacturer"]
            self.model = platform_type["model"]

    def update_channels(self, channels: Dict[str, LGHorizonChannel]):
        """Update the channels list."""
        self._channels = channels

    def register_mqtt(self) -> None:
        """Register the mqtt connection."""
        if not self._mqtt_client.is_connected:
            raise Exception("MQTT client not connected.")
        topic = f"{self._auth.household_id}/{self._mqtt_client.client_id}/status"
        payload = {
            "source": self._mqtt_client.client_id,
            "state": ONLINE_RUNNING,
            "deviceType": "HGO",
        }
        self._mqtt_client.publish_message(topic, json.dumps(payload))

    def set_callback(self, change_callback: Callable) -> None:
        """Set a callback function."""
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
                self._change_callback(self.device_id)
        else:
            self._request_settop_box_state()
        self._request_settop_box_recording_capacity()

    def update_recording_capacity(self, payload) -> None:
        """Updates the recording capacity."""
        if "CPE.capacity" not in payload or "used" not in payload:
            return
        self.recording_capacity = payload["used"]

    def update_with_replay_event(
        self, source_type: str, event: LGHorizonReplayEvent, channel: LGHorizonChannel
    ) -> None:
        """Update box with replay event."""
        self.playing_info.set_source_type(source_type)
        self.playing_info.set_channel(channel.id)
        self.playing_info.set_channel_title(channel.title)
        title = event.title
        if event.episode_name:
            title += f": {event.episode_name}"
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
        """Update box with recording."""
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
        """Update box with vod."""
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
        """Update box with app."""
        self.playing_info.set_source_type(source_type)
        self.playing_info.set_channel(None)
        self.playing_info.set_channel_title(app.title)
        self.playing_info.set_title(app.title)
        self.playing_info.set_image(app.image)
        self.playing_info.reset_progress()
        self._trigger_callback()

    def _trigger_callback(self):
        if self._change_callback:
            _logger.debug("Callback called from box %s", self.device_id)
            self._change_callback(self.device_id)

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
            + self._mqtt_client.client_id
            + '","friendlyDeviceName":"Home Assistant"},'
            + '"status":{"sourceType":"linear","source":{"channelId":"'
            + channel.id
            + '"},"relativePosition":0,"speed":1}}'
        )

        self._mqtt_client.publish_message(
            f"{self._auth.household_id}/{self.device_id}", payload
        )

    def play_recording(self, recording_id):
        """Play recording."""
        payload = (
            '{"id":"'
            + make_id(8)
            + '","type":"CPE.pushToTV","source":{"clientId":"'
            + self._mqtt_client.client_id
            + '","friendlyDeviceName":"Home Assistant"},'
            + '"status":{"sourceType":"nDVR","source":{"recordingId":"'
            + recording_id
            + '"},"relativePosition":0}}'
        )
        self._mqtt_client.publish_message(
            f"{self._auth.household_id}/{self.device_id}", payload
        )

    def send_key_to_box(self, key: str) -> None:
        """Send emulated (remote) key press to settopbox."""
        payload_dict = {
            "type": "CPE.KeyEvent",
            "runtimeType": "key",
            "id": "ha",
            "source": self.device_id.lower(),
            "status": {"w3cKey": key, "eventType": "keyDownUp"},
        }
        payload = json.dumps(payload_dict)
        self._mqtt_client.publish_message(
            f"{self._auth.household_id}/{self.device_id}", payload
        )

    # def _set_unknown_channel_info(self) -> None:
    #     """Set unknown channel info."""
    #     _logger.warning("Couldn't set channel. Channel info set to unknown...")
    #     self.playing_info.set_source_type(BOX_PLAY_STATE_CHANNEL)
    #     self.playing_info.set_channel(None)
    #     self.playing_info.set_title("No information available")
    #     self.playing_info.set_image(None)
    #     self.playing_info.set_paused(False)

    def _request_settop_box_state(self) -> None:
        """Send mqtt message to receive state from settop box."""
        topic = f"{self._auth.household_id}/{self.device_id}"
        payload = {
            "id": make_id(8),
            "type": "CPE.getUiStatus",
            "source": self._mqtt_client.client_id,
        }
        self._mqtt_client.publish_message(topic, json.dumps(payload))

    def _request_settop_box_recording_capacity(self) -> None:
        """Send mqtt message to receive state from settop box."""
        topic = f"{self._auth.household_id}/{self.device_id}"
        payload = {
            "id": make_id(8),
            "type": "CPE.capacity",
            "source": self._mqtt_client.client_id,
        }
        self._mqtt_client.publish_message(topic, json.dumps(payload))


class LGHorizonProfile:
    """LGHorizon profile."""

    profile_id: str = None
    name: str = None
    favorite_channels: list[str] = None

    def __init__(self, json_payload):
        self.profile_id = json_payload["profileId"]
        self.name = json_payload["name"]
        self.favorite_channels = json_payload["favoriteChannels"]


class LGHorizonCustomer:
    """LGHorizon customer"""

    customer_id: str = None
    hashed_customer_id: str = None
    country_id: str = None
    city_id: int = 0
    settop_boxes: list[str] = None
    profiles: Dict[str, LGHorizonProfile] = {}

    def __init__(self, json_payload):
        self.customer_id = json_payload["customerId"]
        self.hashed_customer_id = json_payload["hashedCustomerId"]
        self.country_id = json_payload["countryId"]
        self.city_id = json_payload["cityId"]
        if "assignedDevices" in json_payload:
            self.settop_boxes = json_payload["assignedDevices"]
        if "profiles" in json_payload:
            for profile in json_payload["profiles"]:
                self.profiles[profile["profileId"]] = LGHorizonProfile(profile)
