"""Python client for LGHorizon."""
import logging
from .models.exceptions import LGHorizonApiUnauthorizedError, LGHorizonApiConnectionError
import backoff
from requests import Session
from .models.lghorizon_auth import LGHorizonAuth
from .models.lghorizon_box import LGHorizonBox
from .models.lghorizon_mqtt_client import LGHorizonMqttClient
from .models.lghorizon_customer import LGHorizonCustomer
from .models.lghorizon_channel import LGHorizonChannel
from .models.lghorizon_recording_single import LGHorizonRecordingSingle
from .models.lghorizon_recording_show import LGHorizonRecordingShow
from typing import Dict

# from .const import (
#     ONLINE_RUNNING,
#     ONLINE_STANDBY,
#     MEDIA_KEY_PLAY_PAUSE,
#     MEDIA_KEY_STOP,
#     MEDIA_KEY_CHANNEL_DOWN,
#     MEDIA_KEY_CHANNEL_UP,
#     MEDIA_KEY_POWER,
#     MEDIA_KEY_ENTER,
#     MEDIA_KEY_REWIND,
#     MEDIA_KEY_FAST_FORWARD,
#     MEDIA_KEY_RECORD,
#     COUNTRY_SETTINGS,
# )

# DEFAULT_PORT = 443

_logger = logging.getLogger(__name__)
_supported_platforms = ["EOS", "EOS2", "HORIZON", "APOLLO"]

class LGHorizonApi:
    """Main class for handling connections with LGHorizon Settop boxes."""

    _auth: LGHorizonAuth = None
    _session: Session = None
    settop_boxes: Dict[str, LGHorizonBox] = {}
    _customer: LGHorizonCustomer = None
    _mqttClient: LGHorizonMqttClient = None
    _channels: Dict[str, LGHorizonChannel] = {}

    def __init__(self, username: str, password: str, country_code: str = "nl") -> None:
        """Create LGHorizon API."""
        self.username = username
        self.password = password
        self._session = Session()
        # self.token = None
        # self.session = None
        # self.settop_boxes = {}
        # self.channels = {}
        # self._country_code = country_code
        # self.channels = {}
        # self.country_config = COUNTRY_SETTINGS[self._country_code]
        # self._mqtt_client_connected = False
        # self._base_url = self.country_config["api_url"]
        # self._api_url_session = self._base_url + "/session"
        # self._api_url_token = self._base_url + "/tokens/jwt"
        # self._api_url_channels = self._base_url + "/channels"
        # self._api_url_recordings = self._base_url + "/networkdvrrecordings"
        # self._api_url_authorization = self._base_url + "/authorization"
        # self._last_message_stamp = None
        # self.recording_capacity = None


    @backoff.on_exception(backoff.expo, LGHorizonApiConnectionError, max_tries=3, logger=_logger)
    def _authorize(self) -> None:
        _logger.debug("Authorizing")
        auth_url = "https://prod.spark.ziggogo.tv/auth-service/v1/authorization"
        auth_headers = {
            "x-device-code": "web"
        }
        auth_payload = {
            "password": self.password,
            "username": self.username
        }
        try:
            auth_response = self._session.post(auth_url, headers=auth_headers, json=auth_payload)
        except Exception as ex:
            raise LGHorizonApiConnectionError("Unknown connection failure") from ex
            
        if not auth_response.ok:
            error_json = auth_response.json()
            error = error_json["error"]
            if error and error["statusCode"] == 97401:
                raise LGHorizonApiUnauthorizedError("Invalid credentials")
            elif error:
                raise LGHorizonApiConnectionError(error["message"])
            raise LGHorizonApiConnectionError("Unknown connection error")

        self._auth = LGHorizonAuth(auth_response.json())

    def _obtain_mqtt_token(self):
        mqtt_response = self._do_api_call("https://prod.spark.ziggogo.tv/auth-service/v1/mqtt/token")
        self._auth.mqttToken = mqtt_response["token"]  

    def connect(self) -> None:
        self._authorize()
        self._obtain_mqtt_token()
        self._mqttClient = LGHorizonMqttClient(self._auth, self._on_mqtt_connected, self._on_mqtt_message)
        self._register_customer_and_boxes()
        self._mqttClient.connect()

    def disconnect(self):
        """Disconnect."""
        if not self._mqttClient.is_connected:
            return
        self._mqttClient.disconnect()

    def _on_mqtt_connected(self) -> None:
        box:LGHorizonBox
        for box in self.settop_boxes.values():
            box.register_mqtt()

    def _on_mqtt_message(self, message:str)-> None:
        msg = message
        if "source" in message:
            deviceId = message["source"]
            if not deviceId in self.settop_boxes.keys():
                return
            try:
                if "deviceType" in message and message["deviceType"] == "STB":
                    self.settop_boxes[deviceId].update_state(message)
                if "status" in message:
                    self.settop_boxes[deviceId].update(message)
            except Exception as ex:
                _logger.error("Could not handle status message")
                _logger.error(str(ex))

    @backoff.on_exception(backoff.expo, LGHorizonApiConnectionError, max_tries=3, logger=_logger)
    def _do_api_call(self, url:str, tries:int = 0) -> str:
        if tries > 3:
            raise LGHorizonApiConnectionError("Max retries reached.")
        api_response = self._session.get(url)
        if api_response.ok:
            tries = 0
            return api_response.json()
        elif api_response.status_code == 403:
            self._authorize()
            tries += 1
            self._do_api_call(url, tries)

    def _register_customer_and_boxes(self):
        personalisation_result = self._do_api_call(f"https://prod.spark.ziggogo.tv/eng/web/personalization-service/v1/customer/{self._auth.householdId}?with=profiles%2Cdevices")
        self._customer = LGHorizonCustomer(personalisation_result)
        self._get_channels()
        if not "assignedDevices" in personalisation_result:
            return
        for device in personalisation_result["assignedDevices"]:
            if not device["platformType"] in _supported_platforms:
                continue
            box = LGHorizonBox(device, self._mqttClient,self._auth, self._channels, self._session)
            self.settop_boxes[box.deviceId] = box
            
    def _get_channels(self):
        channels_result = self._do_api_call(f"https://prod.spark.ziggogo.tv/eng/web/linear-service/v2/channels?cityId={self._customer.cityId}&language={self._customer.countryId}&productClass=Orion-DASH")
        for channel in channels_result:
            channel_id = channel["id"]
            self._channels[channel_id] = LGHorizonChannel(channel)

    def get_recording_capacity(self) -> int:
        """Returns remaining recording capacity"""
        try:
            url = f"https://prod.spark.ziggogo.tv/eng/web/recording-service/customers/{self._auth.householdId}/recordings"
            content = self._do_api_call(url)
            if not "quota" in content:
                return None
            quota = content["quota"]
            capacity =  (quota["occupied"] / quota["quota"]) * 100
            self.recording_capacity = round(capacity)
            return self.recording_capacity
        except:
            return None

    # def get_recordings(self):
    #     """Return recordings."""
    #     results = []
    #     url = f"https://prod.spark.ziggogo.tv/eng/web/recording-service/customers/{self._auth.householdId}/recordings"
    #     json_result = self._do_api_call(url)
    #     recordings = json_result["data"]
    #     for recording in recordings:
    #         if recording["type"] == "single":
    #             results.append(LGHorizonRecordingSingle(recording))
    #         elif recording["type"] == "season":
    #             results.append(
    #                 LGHorizonRecordingShow(recording)
    #             )
    #         elif recording["type"] == "show":
    #             results.append(
    #                 self._get_show_recording_summary(recording, "mediaGroupId")
    #             )

    #     return results       