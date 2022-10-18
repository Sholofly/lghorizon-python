"""Python client for LGHorizon."""
import logging
from .exceptions import LGHorizonApiUnauthorizedError, LGHorizonApiConnectionError
import backoff
from requests import Session
from .models import LGHorizonAuth
from .models import LGHorizonBox
from .models import LGHorizonMqttClient
from .models import LGHorizonCustomer
from .models import LGHorizonChannel
from .const import COUNTRY_SETTINGS
from typing import Dict

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
    _country_settings = None

    def __init__(self, username: str, password: str, country_code: str = "nl") -> None:
        """Create LGHorizon API."""
        self.username = username
        self.password = password
        self._session = Session()
        self._country_settings = COUNTRY_SETTINGS[country_code]

    @backoff.on_exception(backoff.expo, LGHorizonApiConnectionError, max_tries=3, logger=_logger)
    def _authorize(self) -> None:
        _logger.debug("Authorizing")
        auth_url = f"{self._country_settings['api_url']}/auth-service/v1/authorization"
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
            else:
                raise LGHorizonApiConnectionError("Unknown connection error")

        self._auth = LGHorizonAuth(auth_response.json())
        _logger.debug("Authorization succeeded")

    def _obtain_mqtt_token(self):
        _logger.debug("Obtain mqtt token...")
        mqtt_response = self._do_api_call(f"{self._country_settings['api_url']}/auth-service/v1/mqtt/token")
        self._auth.mqttToken = mqtt_response["token"]
        _logger.debug(f"MQTT token: {self._auth.mqttToken}")

    def connect(self) -> None:
        _logger.debug("Connect to API")
        self._authorize()
        self._obtain_mqtt_token()
        self._mqttClient = LGHorizonMqttClient(self._auth, self._country_settings, self._on_mqtt_connected, self._on_mqtt_message)
        self._register_customer_and_boxes()
        self._mqttClient.connect()

    def disconnect(self):
        """Disconnect."""
        _logger.debug("Disconnect from API")
        if not self._mqttClient.is_connected:
            return
        self._mqttClient.disconnect()

    def _on_mqtt_connected(self) -> None:
        _logger.debug("Connected to MQTT server. Registering all boxes...")
        box:LGHorizonBox
        for box in self.settop_boxes.values():
            box.register_mqtt()

    def _on_mqtt_message(self, message:str)-> None:
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
        _logger.debug(f"Executing API call to {url}")
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
        else:
            raise LGHorizonApiConnectionError(f"Unable to call {url}. API response:{api_response.status_code} - {api_response.json()}")

    def _register_customer_and_boxes(self):
        _logger.debug("Get personalisation info:")
        personalisation_result = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/personalization-service/v1/customer/{self._auth.householdId}?with=profiles%2Cdevices")
        _logger.debug(personalisation_result)
        self._customer = LGHorizonCustomer(personalisation_result)
        self._get_channels()
        _logger.debug("Registering boxes")
        if not "assignedDevices" in personalisation_result:
            return
        for device in personalisation_result["assignedDevices"]:
            if not device["platformType"] in _supported_platforms:
                continue
            box = LGHorizonBox(device, self._mqttClient,self._auth, self._channels)
            self.settop_boxes[box.deviceId] = box
            _logger.debug(f"Box {box.deviceId} registered...")
            
    def _get_channels(self):
        _logger.debug("Retrieving channels...")
        channels_result = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/linear-service/v2/channels?cityId={self._customer.cityId}&language={self._customer.countryId}&productClass=Orion-DASH")
        for channel in channels_result:
            channel_id = channel["id"]
            self._channels[channel_id] = LGHorizonChannel(channel)
        _logger.debug(f"{len(self._channels)} retrieved.")

    def get_recording_capacity(self) -> int:
        """Returns remaining recording capacity"""
        try:
            url = f"{self._country_settings['api_url']}/eng/web/recording-service/customers/{self._auth.householdId}/recordings"
            content = self._do_api_call(url)
            if not "quota" in content:
                return None
            quota = content["quota"]
            capacity =  (quota["occupied"] / quota["quota"]) * 100
            self.recording_capacity = round(capacity)
            return self.recording_capacity
        except:
            return None   