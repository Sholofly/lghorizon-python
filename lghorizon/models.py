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
    MEDIA_KEY_RECORD
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

    def __init__(self, auth_json:str):
        """Initialize a session."""
        self.householdId = auth_json["householdId"]
        self.accessToken = auth_json["accessToken"]
        self.refreshToken = auth_json["refreshToken"]
        self.refreshTokenExpiry = datetime.fromtimestamp(auth_json["refreshTokenExpiry"])
        self.username = auth_json["username"]
    
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
        """Set sourfce type."""
        self.source_type = source_type

    def reset(self):
        self.channel_id = None
        self.title = None
        self.image = None
        self.source_type = None
        self.paused = False
        self.channel_title = None

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
        self.logo_image = channel_json["logo"]["focused"]
        self.channel_number = channel_json["logicalChannelNumber"]
    
    def get_stream_image(self, channel_json)->str:
        image_stream = channel_json["imageStream"]
        if "full" in image_stream:
            return image_stream["full"]
        if "small" in image_stream:
            return image_stream["small"]
        logo = channel_json["logo"]
        if "focus" in logo:
            return logo["focus"]
        return ""

class LGHorizonRecordingSingle:
    """Represents a single recording."""

    recording_id: str
    title: str
    image: str
    season: int = None
    episode: int = None

    def __init__(self, recording_json):
        """Init the single recording."""
        self.recording_id = recording_json["id"]
        self.title = recording_json["title"]
        self.image = recording_json["poster"]["url"]
        if "season" in recording_json:
            self.season = recording_json["season"]
        if "episode" in recording_json:
            self.episode = recording_json["episode"]

class LGHorizonRecordingShow:
    """Represent a recorderd show."""

    title: str
    showId: str
    channelId: str
    image: str
    children: List[LGHorizonRecordingSingle] = []
    episode_count: int

    def __init__(self, recording_json):
        """Init recorder show."""
        self.showId = recording_json["showId"]
        self.title = recording_json["title"]
        self.image = recording_json["poster"]["url"]
        self.episode_count = recording_json["noOfEpisodes"]
        

    def append_child(self, season_recording: LGHorizonRecordingSingle):
        """Append child."""
        self.children.append(season_recording)

class LGHorizonRecordingSeason:
    """Represent a recorderd show."""

    title: str
    Id: str
    channelId: str
    image: str
    children: List[LGHorizonRecordingSingle] = []
    episode_count: int

    def __init__(self, recording_json):
        """Init recorder show."""
        self.showId = recording_json["Id"]
        self.title = recording_json["title"]
        self.image = recording_json["poster"]["url"]
        self.episode_count = recording_json["noOfEpisodes"]
        

    def append_child(self, season_recording: LGHorizonRecordingSingle):
        """Append child."""
        self.children.append(season_recording)       

class LGHorizonMqttClient:
    _brokerUrl:str = None
    _mqtt_client :mqtt.Client
    _auth: LGHorizonAuth
    clientId: str = None
    _on_connected_callback: Callable = None
    _on_message_callback: Callable[[str],None] = None

    @property
    def is_connected(self):
        return self._mqtt_client.is_connected

    def __init__(self, auth:LGHorizonAuth, country_settings:Dict[str,Any], on_connected_callback:Callable = None, on_message_callback:Callable[[str],None] = None):
        self._auth = auth
        self._brokerUrl = "obomsg.prod.nl.horizon.tv"
        self.clientId = make_id()
        self._mqtt_client = mqtt.Client(self.clientId, transport="websockets")
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
            self._mqtt_client.subscribe(self._auth.householdId + "/+/networkRecordings/capacity")
            self._mqtt_client.subscribe(self._auth.householdId + "/watchlistService")
            self._mqtt_client.subscribe(self._auth.householdId + "/purchaseService")
            self._mqtt_client.subscribe(self._auth.householdId + "/personalizationService")
            self._mqtt_client.subscribe(self._auth.householdId + "/recordingStatus")
            self._mqtt_client.subscribe(self._auth.householdId + "/recordingStatus/lastUserAction")
            if self._on_connected_callback:
                self._on_connected_callback()
        elif resultCode == 5:
            self._mqtt_client.username_pw_set(self._auth.householdId, self._auth.mqttToken)
            self.connect()
            raise Exception("Could not connect to Mqtt server")
    
    def connect(self) -> None:
        self._mqtt_client.connect(self._brokerUrl, 443)
        self._mqtt_client.loop_start()
    
    def _on_client_message(self, client, userdata, message):
        """Handle messages received by mqtt client."""
        _logger.debug(f"Received MQTT message. Topic: {message.topic}")
        jsonPayload = json.loads(message.payload)
        _logger.debug(f"Message: {jsonPayload}")
        if self._on_message_callback:
            self._on_message_callback(jsonPayload)

    def publish_message(self, topic:str, json_payload:str) -> None:
        self._mqtt_client.publish(topic, json_payload)
        
    def disconnect(self) -> None:
        if self._mqtt_client.is_connected:
            self._mqtt_client.disconnect()

class LGHorizonBox:

    deviceId:str
    hashedCPEId:str
    deviceFriendlyName:str
    state: str = None
    playing_info: LGHorizonPlayingInfo = LGHorizonPlayingInfo()
    
    _mqtt_client:LGHorizonMqttClient
    _change_callback: Callable = None
    _auth: LGHorizonAuth = None
    _channels:Dict[str, LGHorizonChannel] = None
    _message_stamp = None
    
    def __init__(self, box_json:str, mqtt_client:LGHorizonMqttClient, auth:LGHorizonAuth, channels:Dict[str, LGHorizonChannel]):
        self.deviceId = box_json["deviceId"]
        self.hashedCPEId = box_json["hashedCPEId"]
        self.deviceFriendlyName = box_json["settings"]["deviceFriendlyName"]
        self._mqtt_client = mqtt_client
        self._auth = auth
        self._channels = channels
        
    def register_mqtt(self)->None:
        if not self._mqtt_client.is_connected:
            raise Exception("MQTT client not connected.")
        topic = f"{self._auth.householdId}/{self._mqtt_client.clientId}/status"
        payload = {
            "source": self._mqtt_client.clientId,
            "state": ONLINE_RUNNING,
            "deviceType": "HGO",
        }   
        self._mqtt_client.publish_message(topic, json.dumps(payload))
    
    def set_callback(self, change_callback:Callable) -> None:
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
    
    def update(self, payload):
        deviceId = payload["source"]
        if deviceId != self.deviceId:
            return
        statusPayload = payload["status"]
        if "uiStatus" not in statusPayload:
            return
        message_stamp = payload["messageTimeStamp"]
        if self._message_stamp and self._message_stamp > message_stamp:
            return
        self._message_stamp = message_stamp
        uiStatus = statusPayload["uiStatus"]
        if uiStatus == "mainUI":
            playerState = statusPayload["playerState"]
            if "sourceType" not in playerState or "source" not in playerState:
                return
            source_type = playerState["sourceType"]
            state_source = playerState["source"]
            speed = playerState["speed"]
            if source_type == BOX_PLAY_STATE_REPLAY:
                self.playing_info.set_source_type(BOX_PLAY_STATE_REPLAY)
                if state_source is None or "eventId" not in state_source:
                    _logger.warning("No eventId in stateSource")
                    _logger.warning("State update was skipped ")
                    return
                eventId = state_source["eventId"]
                listing = self._get_listing(eventId)
                channel_id = listing["channelId"]
                if channel_id is not None and channel_id in self._channels.keys():
                    self.playing_info.set_channel(channel_id)
                    channel:LGHorizonChannel = self._channels[channel_id]
                    self.playing_info.set_channel_title(channel.title)
                    self.playing_info.set_title("ReplayTV: " + listing["title"])
                    self.playing_info.set_image(channel.stream_image)
                else:
                    self._set_unknown_channel_info()
            elif source_type == BOX_PLAY_STATE_DVR:
                self.playing_info.set_source_type(BOX_PLAY_STATE_DVR)
                if state_source is None or "recordingId" not in state_source:
                    _logger.warning(
                        "No recordingId in stateSource,State update was skipped."
                    )
                    return
                recordingId = state_source["recordingId"]
                listing = self._get_listing(recordingId)
                channel_id = listing["channelId"]
                if channel_id is not None and channel_id in self._channels.keys():
                    self.playing_info.set_channel(channel_id)
                    channel:LGHorizonChannel = self._channels[channel_id]
                    self.playing_info.set_title(
                        "Recording: " + listing["title"]
                    )
                    self.playing_info.set_image(channel.stream_image)
                else:
                    self._set_unknown_channel_info()
            elif source_type == BOX_PLAY_STATE_BUFFER:
                self.playing_info.set_source_type(BOX_PLAY_STATE_BUFFER)
                if state_source is None or "channelId" not in state_source:
                    _logger.warning(
                        "No channelId in stateSource. State update was skipped."
                    )
                    return
                channel_id = state_source["channelId"]
                if channel_id is not None and channel_id in self._channels.keys():
                    self.playing_info.set_channel(channel_id)
                    channel:LGHorizonChannel = self._channels[channel_id]
                    self.playing_info.set_channel_title(channel.title)
                    eventId = state_source["eventId"]
                    listing = self._get_listing(eventId)
                    self.playing_info.set_title("Delayed: " + listing["title"])
                    self.playing_info.set_image(channel.stream_image)
                else:
                    self._set_unknown_channel_info()
            elif source_type == BOX_PLAY_STATE_CHANNEL:
                self.playing_info.set_source_type(BOX_PLAY_STATE_CHANNEL)
                if state_source is None or "channelId" not in state_source:
                    _logger.warning(
                        "No channelId in state_source. State update was skipped."
                    )
                    return
                channel_id = state_source["channelId"]
                eventId = state_source["eventId"]
                if channel_id is not None and channel_id in self._channels.keys():
                    channel = self._channels[channel_id]
                    listing = self._get_listing(eventId)
                    self.playing_info.set_channel(channel_id)
                    self.playing_info.set_channel_title(channel.title)
                    self.playing_info.set_title(listing["title"])
                    self.playing_info.set_image(channel.stream_image)
                else:
                    _logger.debug(
                        f"channelId {channel_id} not in channelsList: {self._channels.keys()}"
                    )
                    self._set_unknown_channel_info()                
            elif source_type == BOX_PLAY_STATE_VOD:
                self.playing_info.set_source_type(BOX_PLAY_STATE_VOD)
                title_id = state_source["titleId"]
                # mediagroup_content = self._get_mediagroup(title_id)
                self.playing_info.set_channel(None)
                self.playing_info.set_channel_title("VOD")
                # self.playing_info.set_title(self._get_mediagroup_title(mediagroup_content))
                # self.playing_info.set_image(self._get_mediagroup_image(mediagroup_content))
                pass
            else:
                self._set_unknown_channel_info()
            self.playing_info.set_paused(speed == 0)
        elif uiStatus == "apps":
            appsState = statusPayload["appsState"]
            logoPath = appsState["logoPath"]
            if not logoPath.startswith("http:"):
                logoPath = "https:" + logoPath
            self.playing_info.set_source_type(BOX_PLAY_STATE_APP)
            self.playing_info.set_channel(None)
            self.playing_info.set_channel_title(appsState["appName"])
            self.playing_info.set_title(appsState["appName"])
            self.playing_info.set_image(logoPath)
            self.playing_info.set_paused(False)

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

    def set_channel(self, source:str) -> None:
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

        self._mqtt_client.publish_message(f"{self._auth.householdId}/{self.deviceId}", payload)

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
        self._mqtt_client.publish_message(f"{self._auth.householdId}/{self.deviceId}", payload)

    def send_key_to_box(self, key: str) -> None:
        """Send emulated (remote) key press to settopbox."""
        payload = (
            '{"type":"CPE.KeyEvent","status":{"w3cKey":"'
            + key
            + '","eventType":"keyDownUp"}}'
        )
        self._mqtt_client.publish_message(f"{self._auth.householdId}/{self.deviceId}", payload)

    def _set_unknown_channel_info(self) -> None:
        """Set unknown channel info."""
        _logger.warning("Couldn't set channel. Channel info set to unknown...")
        self.playing_info.set_source_type(BOX_PLAY_STATE_CHANNEL)
        self.playing_info.set_channel(None)
        self.playing_info.set_title("No information available")
        self.playing_info.set_image(None)
        self.playing_info.set_paused(False)

    def _get_listing(self, listing_id):
        """Get listing."""
        url = "https://prod.spark.ziggogo.tv/eng/web/linear-service/v2/replayEvent/"+ listing_id + "?returnLinearContent=true&language=nl"
        response = requests.get(url)
        if response.ok:
            return response.json()
        return None

    def _request_settop_box_state(self) -> None:
        """Send mqtt message to receive state from settop box."""
        topic = f"{self._auth.householdId}/{self.deviceId}"
        payload = {
            "id": make_id(8),
            "type": "CPE.getUiStatus",
            "source": self._mqtt_client.clientId,
        }
        self._mqtt_client.publish_message(topic, json.dumps(payload))

class LGHorizonCustomer:
    customerId:str = None
    hashedCustomerId:str = None 
    countryId: str = None
    cityId: int = 0
    settop_boxes: Dict[str, LGHorizonBox] = None

    def __init__(self, json_payload):
        self.customerId = json_payload["customerId"]
        self.hashedCustomerId = json_payload["hashedCustomerId"]
        self.countryId = json_payload["countryId"]
        self.cityId = json_payload["cityId"]
        if not "assignedDevices" in json_payload:
            return


