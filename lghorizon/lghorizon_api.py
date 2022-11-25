"""Python client for LGHorizon."""
import logging
import json
import sys, traceback
from .exceptions import LGHorizonApiUnauthorizedError, LGHorizonApiConnectionError
import backoff
from requests import Session, exceptions as request_exceptions
import re
from .models import (
    LGHorizonAuth, 
    LGHorizonBox,
    LGHorizonMqttClient,
    LGHorizonCustomer,
    LGHorizonChannel,
    LGHorizonReplayEvent,
    LGHorizonRecordingSingle,
    LGHorizonVod,
    LGHorizonApp,
    LGHorizonBaseRecording,
    LGHorizonRecordingListSeasonShow,
    LGHorizonRecordingEpisode,
    LGHorizonRecordingShow
    )

from .const import (
    COUNTRY_SETTINGS,
    BOX_PLAY_STATE_BUFFER,
    BOX_PLAY_STATE_CHANNEL,
    BOX_PLAY_STATE_DVR,
    BOX_PLAY_STATE_REPLAY,
    BOX_PLAY_STATE_VOD,
    RECORDING_TYPE_SINGLE,
    RECORDING_TYPE_SEASON,
    RECORDING_TYPE_SHOW)
from typing import Any, Dict, List

_logger = logging.getLogger(__name__)
_supported_platforms = ["EOS", "EOS2", "HORIZON", "APOLLO"]

class LGHorizonApi:
    """Main class for handling connections with LGHorizon Settop boxes."""

    _auth: LGHorizonAuth = LGHorizonAuth()
    _session: Session = None
    settop_boxes: Dict[str, LGHorizonBox] = {}
    _customer: LGHorizonCustomer = None
    _mqttClient: LGHorizonMqttClient = None
    _channels: Dict[str, LGHorizonChannel] = {}
    _country_settings = None
    _country_code:str = None
    recording_capacity:int = None
    _entitlements:List[str] = []

    def __init__(self, username: str, password: str, country_code: str = "nl") -> None:
        """Create LGHorizon API."""
        self.username = username
        self.password = password
        self._session = Session()
        self._country_settings = COUNTRY_SETTINGS[country_code]
        self._country_code = country_code

    @backoff.on_exception(backoff.expo, LGHorizonApiConnectionError, max_tries=3, logger=_logger)
    def _authorize(self) -> None:
        if self._country_code == 'be-nl':
            self.authorize_telenet()
        elif self._country_code == 'gb':
            self.authorize_gb()
        else:
            self._authorize_default()

    def _authorize_default(self) -> None:
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

        self._auth.fill(auth_response.json())
        _logger.debug("Authorization succeeded")

    def authorize_gb(self):

        try:
            login_session = Session()
####################################
            _logger.debug("Step 1 - Get Authorization data")
            auth_url = f"{self._country_settings['api_url']}/authorization"
            auth_response = login_session.get(auth_url)
            if not auth_response.ok:
                raise LGHorizonApiConnectionError("Can't connect to authorization URL")
            auth_response_json = auth_response.json()
            auth_session = auth_response_json["session"]
            auth_state = auth_session["state"]
            authorizationUri = auth_session["authorizationUri"]
            authValidtyToken = auth_session["validityToken"]

####################################
            _logger.debug("Step 2 - Get Authorization cookie")

            auth_cookie_response = login_session.get(authorizationUri)
            if not auth_cookie_response.ok:
                raise LGHorizonApiConnectionError("Can't connect to authorization URL")
####################################       
            _logger.debug("Step 3 - Login")
            payload = {
                "username": self.username,
                "credential": self.password
            }
            headers = {
                "accept": "application/json; charset=UTF-8, */*",
            },
            
            login_response = login_session.post(
                self._country_settings["oauth_url"], json.dumps(payload), headers="headers", allow_redirects=False
            )
            if not login_response.ok:
                raise LGHorizonApiConnectionError("Can't connect to authorization URL")
            
            if not "x-redirect-location" in login_response.headers:
                raise LGHorizonApiConnectionError("No redirect location in headers.")
            
            redirect_url = login_response.headers["x-redirect-location"]
####################################
            _logger.debug("Step 4 - Follow redirect")
            redirect_response = login_session.get(redirect_url, allow_redirects=False)
            if not "location" in success_url:
                raise LGHorizonApiConnectionError("No success url in redirect.")
 ####################################           
            _logger.debug("Step 5 - Extrect auth code")
            success_url = redirect_response.headers["location"]
            codeMatches = re.findall(r"code=(.*)&", success_url)
            if len(codeMatches) == 0:
                raise LGHorizonApiConnectionError("No code in redirect headers")
            authorizationCode = codeMatches[0]
####################################
            _logger.debug("Step 6 - Post auth data with valid code")
            new_payload = {
                "authorizationGrant":{
                    "authorizationCode":authorizationCode,
                    "validityToken":authValidtyToken,
                    "state": auth_state
                }
            }
            headers = {
                "content-type":"application/json",
            }
            post_result = login_session.post(auth_url, json.dumps(new_payload), headers = headers)
            self._auth.fill(post_result.json())
            self._session.cookies["ACCESSTOKEN"] = self._auth.accessToken
####################################          
        except Exception as ex:
            pass 

    def authorize_telenet(self):

        try:
            login_session = Session()
            #Step 1 - Get Authorization data
            _logger.debug("Step 1 - Get Authorization data")
            auth_url = f"{self._country_settings['api_url']}/auth-service/v1/sso/authorization"
            auth_response = login_session.get(auth_url)
            if not auth_response.ok:
                raise LGHorizonApiConnectionError("Can't connect to authorization URL")
            auth_response_json = auth_response.json()
            authorizationUri = auth_response_json["authorizationUri"]
            authValidtyToken = auth_response_json["validityToken"]

            #Step 2 - Get Authorization cookie
            _logger.debug("Step 2 - Get Authorization cookie")

            auth_cookie_response = login_session.get(authorizationUri)
            if not auth_cookie_response.ok:
                raise LGHorizonApiConnectionError("Can't connect to authorization URL")
            
            _logger.debug("Step 3 - Login")

            username_fieldname = self._country_settings["oauth_username_fieldname"]
            pasword_fieldname = self._country_settings["oauth_password_fieldname"]

            payload = {
                username_fieldname: self.username,
                pasword_fieldname: self.password,
                "rememberme": 'true'
            }

            
            login_response = login_session.post(
                self._country_settings["oauth_url"], payload, allow_redirects=False
            )
            if not login_response.ok:
                raise LGHorizonApiConnectionError("Can't connect to authorization URL")
            redirect_url = login_response.headers[self._country_settings["oauth_redirect_header"]]
            
            redirect_response = login_session.get(redirect_url, allow_redirects=False)
            success_url = redirect_response.headers[self._country_settings["oauth_redirect_header"]]
            codeMatches = re.findall(r"code=(.*)&", success_url)
            
            authorizationCode = codeMatches[0]

            new_payload = {
                "authorizationGrant":{
                    "authorizationCode":authorizationCode,
                    "validityToken":authValidtyToken
                }
            }
            headers = {
                "content-type":"application/json",
            }
            post_result = login_session.post(auth_url, json.dumps(new_payload), headers = headers)
            self._auth.fill(post_result.json())
            self._session.cookies["ACCESSTOKEN"] = self._auth.accessToken
        except Exception as ex:
            pass 

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
                    self._handle_box_update(deviceId, message)
            except Exception as ex:
                _logger.error("Could not handle status message")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                _logger.error(f"Full message: {str(message)}")
                _logger.error(repr(traceback.format_exception(etype=exc_type, value = exc_value, tb=exc_traceback)))
                self.settop_boxes[deviceId].playing_info.reset()
                self.settop_boxes[deviceId].playing_info.set_paused(False)

    def _handle_box_update(self, deviceId:str, raw_message:Any) -> None:
        statusPayload = raw_message["status"]
        if "uiStatus" not in statusPayload:
            return
        uiStatus = statusPayload["uiStatus"]
        if uiStatus == "mainUI":
            playerState = statusPayload["playerState"]
            if "sourceType" not in playerState or "source" not in playerState:
                return
            source_type = playerState["sourceType"]
            state_source = playerState["source"]
            self.settop_boxes[deviceId].playing_info.set_paused(playerState["speed"] == 0)
            if source_type in (
                BOX_PLAY_STATE_CHANNEL,
                BOX_PLAY_STATE_BUFFER,
                BOX_PLAY_STATE_REPLAY
                ):
                eventId = state_source["eventId"]
                raw_replay_event = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/linear-service/v2/replayEvent/{eventId}?returnLinearContent=true&language={self._country_settings['language']}")
                replayEvent = LGHorizonReplayEvent(raw_replay_event)
                channel = self._channels[replayEvent.channelId]
                self.settop_boxes[deviceId].update_with_replay_event(source_type, replayEvent, channel)
            elif source_type == BOX_PLAY_STATE_DVR:
                recordingId = state_source["recordingId"]
                raw_recording = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/recording-service/customers/{self._auth.householdId}/details/single/{recordingId}?profileId=4504e28d-c1cb-4284-810b-f5eaab06f034&language={self._country_settings['language']}")
                recording = LGHorizonRecordingSingle(raw_recording)
                channel = self._channels[recording.channelId]
                self.settop_boxes[deviceId].update_with_recording(source_type, recording, channel)
            elif source_type == BOX_PLAY_STATE_VOD:
                titleId = state_source["titleId"]
                raw_vod = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/vod-service/v2/detailscreen/{titleId}?language={self._country_settings['language']}&profileId=4504e28d-c1cb-4284-810b-f5eaab06f034&cityId={self._customer.cityId}")
                vod = LGHorizonVod(raw_vod)
                self.settop_boxes[deviceId].update_with_vod(source_type, vod)
        elif uiStatus == "apps":
            app = LGHorizonApp(statusPayload["appsState"])
            self.settop_boxes[deviceId].update_with_app('app', app)     

    @backoff.on_exception(backoff.expo, LGHorizonApiConnectionError, max_tries=3, logger=_logger)
    def _do_api_call(self, url:str, tries:int = 0) -> str:
        _logger.info(f"Executing API call to {url}")
        try:
            api_response = self._session.get(url)
            api_response.raise_for_status()
        except request_exceptions.HTTPError as httpEx:
            self._authorize()
            raise LGHorizonApiConnectionError(f"Unable to call {url}. Error:{str(httpEx)}")
        except Exception as ex:
            self._authorize()
            raise LGHorizonApiConnectionError(f"Unable to call {url}. Error:{str(ex)}")
        json_response = api_response.json()
        _logger.debug(f"Result API call: {json_response}")
        return json_response
       
    def _register_customer_and_boxes(self):
        _logger.info("Get personalisation info...")
        personalisation_result = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/personalization-service/v1/customer/{self._auth.householdId}?with=profiles%2Cdevices")
        _logger.debug(f"Personalisation result: {personalisation_result}")
        self._customer = LGHorizonCustomer(personalisation_result)
        self._get_channels()
        if not "assignedDevices" in personalisation_result:
            _logger.warning("No boxes found.")
            return
        _logger.info("Registering boxes")
        for device in personalisation_result["assignedDevices"]:
            platform_type = device["platformType"]
            if not platform_type in _supported_platforms:
                continue
            if "platform_types" in self._country_settings and platform_type in self._country_settings["platform_types"]:
                platformType = self._country_settings["platform_types"][platform_type]
            else:
                platformType = None
            box = LGHorizonBox(device, platformType, self._mqttClient,self._auth, self._channels)
            self.settop_boxes[box.deviceId] = box
            _logger.info(f"Box {box.deviceId} registered...")
            
    def _get_channels(self):
        self._update_entitlements()
        _logger.info("Retrieving channels...")
        channels_result = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/linear-service/v2/channels?cityId={self._customer.cityId}&language={self._country_settings['language']}&productClass=Orion-DASH")
        for channel in channels_result:
            if "isRadio" in channel and channel["isRadio"]:
                continue
            common_entitlements = list(set(self._entitlements) & set(channel["linearProducts"]))
            if len(common_entitlements) == 0:
                continue
            channel_id = channel["id"]
            self._channels[channel_id] = LGHorizonChannel(channel)
        _logger.info(f"{len(self._channels)} retrieved.")

    def _get_replay_event(self, listingId) -> Any: 
        """Get listing."""
        _logger.info("Retrieving replay event details...")
        response = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/linear-service/v2/replayEvent/{listingId}?returnLinearContent=true&language={self._country_settings['language']}")
        _logger.info("Replay event details retrieved")
        return response

    def  get_recording_capacity(self) -> int:
        """Returns remaining recording capacity"""
        try:
            _logger.info("Retrieving recordingcapacity...")
            quota_content = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/recording-service/customers/{self._auth.householdId}/quota")
            if not "quota" in quota_content and not "occupied" in quota_content:
                _logger.error("Unable to fetch recording capacity...")
                return None
            capacity =  (quota_content["occupied"] / quota_content["quota"]) * 100
            self.recording_capacity = round(capacity)
            _logger.debug(f"Remaining recordingcapacity {self.recording_capacity}%")
            return self.recording_capacity
        except:
            _logger.error("Unable to fetch recording capacity...")
            return None
    
    def get_recordings(self) -> List[LGHorizonBaseRecording]:
        _logger.info("Retrieving recordings...")
        recording_content = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/recording-service/customers/{self._auth.householdId}/recordings?sort=time&sortOrder=desc&language={self._country_settings['language']}")
        recordings= []
        for recording_data_item in recording_content['data']:
            type = recording_data_item['type']
            if type == RECORDING_TYPE_SINGLE:
                recordings.append(LGHorizonRecordingSingle(recording_data_item))
            elif type in (RECORDING_TYPE_SEASON, RECORDING_TYPE_SHOW):
                recordings.append(LGHorizonRecordingListSeasonShow(recording_data_item))
        _logger.info(F"{len(recordings)} recordings retrieved...")
        return recordings

    def get_recording_show(self, showId:str) -> list[LGHorizonRecordingSingle]:
        _logger.info("Retrieving show recordings...")
        show_recording_content = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/recording-service/customers/{self._auth.householdId}/episodes/shows/{showId}?source=recording&language=nl&sort=time&sortOrder=asc")
        recordings = []
        for item in show_recording_content["data"]:
            if item['source'] == 'show':
                recordings.append(LGHorizonRecordingShow(item))
            else:
                recordings.append(LGHorizonRecordingEpisode(item))
        _logger.info(F"{len(recordings)} showrecordings retrieved...")
        return recordings
    
    def _update_entitlements(self) -> None:
        _logger.info("Retrieving entitlements...")
        entitlements_json = self._do_api_call(f"{self._country_settings['api_url']}/eng/web/purchase-service/v2/customers/{self._auth.householdId}/entitlements?enableDaypass=true")
        self._entitlements.clear()
        for entitlement in entitlements_json["entitlements"]:
            self._entitlements.append(entitlement["id"])
