"""Python client for LGHorizon."""

import logging
import json
import sys, traceback
from .exceptions import (
    LGHorizonApiUnauthorizedError,
    LGHorizonApiConnectionError,
    LGHorizonApiLockedError,
)
import backoff
from requests import Session, exceptions as request_exceptions
from paho.mqtt.client import WebsocketConnectionError
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
    LGHorizonRecordingShow,
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
    RECORDING_TYPE_SHOW,
)
from typing import Any, Callable, Dict, List

_logger = logging.getLogger(__name__)
_supported_platforms = ["EOS", "EOS2", "HORIZON", "APOLLO"]


class LGHorizonApi:
    """Main class for handling connections with LGHorizon Settop boxes."""

    _auth: LGHorizonAuth = None
    _session: Session = None
    settop_boxes: Dict[str, LGHorizonBox] = None
    customer: LGHorizonCustomer = None
    _mqttClient: LGHorizonMqttClient = None
    _channels: Dict[str, LGHorizonChannel] = None
    _country_settings = None
    _country_code: str = None
    recording_capacity: int = None
    _entitlements: List[str] = None
    _identifier: str = None
    _config: str = None
    _refresh_callback: Callable = None
    _profile_id: str = None

    def __init__(
        self,
        username: str,
        password: str,
        country_code: str = "nl",
        identifier: str = None,
        refresh_token=None,
        profile_id=None,
    ) -> None:
        """Create LGHorizon API."""
        self.username = username
        self.password = password
        self.refresh_token = refresh_token
        self._session = Session()
        self._country_settings = COUNTRY_SETTINGS[country_code]
        self._country_code = country_code
        self._auth = LGHorizonAuth()
        self.settop_boxes = {}
        self._channels = {}
        self._entitlements = []
        self._identifier = identifier
        self._profile_id = profile_id

    def _authorize(self) -> None:
        ctry_code = self._country_code[0:2]
        if ctry_code == "be":
            self.authorize_telenet()
        elif ctry_code == "gb":
            self.authorize_gb()
        else:
            self._authorize_default()

    def _authorize_default(self) -> None:
        _logger.debug("Authorizing")
        auth_url = f"{self._country_settings['api_url']}/auth-service/v1/authorization"
        auth_headers = {"x-device-code": "web"}
        auth_payload = {"password": self.password, "username": self.username}
        try:
            auth_response = self._session.post(
                auth_url, headers=auth_headers, json=auth_payload
            )
        except Exception as ex:
            raise LGHorizonApiConnectionError("Unknown connection failure") from ex

        if not auth_response.ok:
            error_json = auth_response.json()
            error = error_json["error"]
            if error and error["statusCode"] == 97401:
                raise LGHorizonApiUnauthorizedError("Invalid credentials")
            elif error and error["statusCode"] == 97117:
                raise LGHorizonApiLockedError("Account locked")
            elif error:
                raise LGHorizonApiConnectionError(error["message"])
            else:
                raise LGHorizonApiConnectionError("Unknown connection error")

        self._auth.fill(auth_response.json())
        _logger.debug("Authorization succeeded")

    def authorize_gb(self) -> None:
        _logger.debug("Authorizing via refresh")
        refresh_url = (
            f"{self._country_settings['api_url']}/auth-service/v1/authorization/refresh"
        )
        headers = {"content-type": "application/json", "charset": "utf-8"}
        payload = '{"refreshToken":"' + self.refresh_token + '"}'

        try:
            auth_response = self._session.post(
                refresh_url, headers=headers, data=payload
            )
        except Exception as ex:
            raise LGHorizonApiConnectionError("Unknown connection failure") from ex

        if not auth_response.ok:
            _logger.debug("response %s", auth_response)
            error_json = auth_response.json()
            error = None
            if "error" in error_json:
                error = error_json["error"]
            if error and error["statusCode"] == 97401:
                raise LGHorizonApiUnauthorizedError("Invalid credentials")
            elif error:
                raise LGHorizonApiConnectionError(error["message"])
            else:
                raise LGHorizonApiConnectionError("Unknown connection error")

        self._auth.fill(auth_response.json())
        self.refresh_token = self._auth.refreshToken
        self._session.cookies["ACCESSTOKEN"] = self._auth.accessToken

        if self._refresh_callback:
            self._refresh_callback()

        _logger.debug("Authorization succeeded")

    def set_callback(self, refresh_callback: Callable) -> None:
        self._refresh_callback = refresh_callback

    def authorize_telenet(self):
        try:
            login_session = Session()
            # Step 1 - Get Authorization data
            _logger.debug("Step 1 - Get Authorization data")
            auth_url = (
                f"{self._country_settings['api_url']}/auth-service/v1/sso/authorization"
            )
            auth_response = login_session.get(auth_url)
            if not auth_response.ok:
                raise LGHorizonApiConnectionError("Can't connect to authorization URL")
            auth_response_json = auth_response.json()
            authorizationUri = auth_response_json["authorizationUri"]
            authValidtyToken = auth_response_json["validityToken"]

            # Step 2 - Get Authorization cookie
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
                "rememberme": "true",
            }

            login_response = login_session.post(
                self._country_settings["oauth_url"], payload, allow_redirects=False
            )
            if not login_response.ok:
                raise LGHorizonApiConnectionError("Can't connect to authorization URL")
            redirect_url = login_response.headers[
                self._country_settings["oauth_redirect_header"]
            ]

            if not self._identifier is None:
                redirect_url += f"&dtv_identifier={self._identifier}"
            redirect_response = login_session.get(redirect_url, allow_redirects=False)
            success_url = redirect_response.headers[
                self._country_settings["oauth_redirect_header"]
            ]
            codeMatches = re.findall(r"code=(.*)&", success_url)

            authorizationCode = codeMatches[0]

            new_payload = {
                "authorizationGrant": {
                    "authorizationCode": authorizationCode,
                    "validityToken": authValidtyToken,
                }
            }
            headers = {
                "content-type": "application/json",
            }
            post_result = login_session.post(
                auth_url, json.dumps(new_payload), headers=headers
            )
            self._auth.fill(post_result.json())
            self._session.cookies["ACCESSTOKEN"] = self._auth.accessToken
        except Exception as ex:
            pass

    def _obtain_mqtt_token(self):
        _logger.debug("Obtain mqtt token...")
        mqtt_auth_url = self._config["authorizationService"]["URL"]
        mqtt_response = self._do_api_call(f"{mqtt_auth_url}/v1/mqtt/token")
        self._auth.mqttToken = mqtt_response["token"]
        _logger.debug(f"MQTT token: {self._auth.mqttToken}")

    @backoff.on_exception(
        backoff.expo,
        BaseException,
        jitter=None,
        max_tries=3,
        logger=_logger,
        giveup=lambda e: isinstance(
            e, (LGHorizonApiLockedError, LGHorizonApiUnauthorizedError)
        ),
    )
    def connect(self) -> None:
        self._config = self._get_config(self._country_code)
        _logger.debug("Connect to API")
        self._authorize()
        self._obtain_mqtt_token()
        self._mqttClient = LGHorizonMqttClient(
            self._auth,
            self._config["mqttBroker"]["URL"],
            self._on_mqtt_connected,
            self._on_mqtt_message,
        )

        self._register_customer_and_boxes()
        self._mqttClient.connect()

    def disconnect(self):
        """Disconnect."""
        _logger.debug("Disconnect from API")
        if not self._mqttClient or not self._mqttClient.is_connected:
            return
        self._mqttClient.disconnect()

    def _on_mqtt_connected(self) -> None:
        _logger.debug("Connected to MQTT server. Registering all boxes...")
        box: LGHorizonBox
        for box in self.settop_boxes.values():
            box.register_mqtt()

    def _on_mqtt_message(self, message: str, topic: str) -> None:
        if "source" in message:
            deviceId = message["source"]
            if not isinstance(deviceId, str):
                _logger.debug("ignoring message - not a string")
                return
            if not deviceId in self.settop_boxes.keys():
                return
            try:
                if "deviceType" in message and message["deviceType"] == "STB":
                    self.settop_boxes[deviceId].update_state(message)
                if "status" in message:
                    self._handle_box_update(deviceId, message)
            except Exception:
                _logger.exception("Could not handle status message")
                _logger.warning(f"Full message: {str(message)}")
                self.settop_boxes[deviceId].playing_info.reset()
                self.settop_boxes[deviceId].playing_info.set_paused(False)
        elif "CPE.capacity" in message:
            splitted_topic = topic.split("/")
            if len(splitted_topic) != 4:
                return
            deviceId = splitted_topic[1]
            if not deviceId in self.settop_boxes.keys():
                return
            self.settop_boxes[deviceId].update_recording_capacity(message)

    def _handle_box_update(self, deviceId: str, raw_message: Any) -> None:
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
            self.settop_boxes[deviceId].playing_info.set_paused(
                playerState["speed"] == 0
            )
            if (
                source_type
                in (
                    BOX_PLAY_STATE_CHANNEL,
                    BOX_PLAY_STATE_BUFFER,
                    BOX_PLAY_STATE_REPLAY,
                )
                and "eventId" in state_source
            ):
                eventId = state_source["eventId"]
                raw_replay_event = self._do_api_call(
                    f"{self._config['linearService']['URL']}/v2/replayEvent/{eventId}?returnLinearContent=true&language={self._country_settings['language']}"
                )
                replayEvent = LGHorizonReplayEvent(raw_replay_event)
                channel = self._channels[replayEvent.channelId]
                self.settop_boxes[deviceId].update_with_replay_event(
                    source_type, replayEvent, channel
                )
            elif source_type == BOX_PLAY_STATE_DVR:
                recordingId = state_source["recordingId"]
                session_start_time = state_source["sessionStartTime"]
                session_end_time = state_source["sessionEndTime"]
                last_speed_change_time = playerState["lastSpeedChangeTime"]
                relative_position = playerState["relativePosition"]
                raw_recording = self._do_api_call(
                    f"{self._config['recordingService']['URL']}/customers/{self._auth.householdId}/details/single/{recordingId}?profileId=4504e28d-c1cb-4284-810b-f5eaab06f034&language={self._country_settings['language']}"
                )
                recording = LGHorizonRecordingSingle(raw_recording)
                channel = self._channels[recording.channelId]
                self.settop_boxes[deviceId].update_with_recording(
                    source_type,
                    recording,
                    channel,
                    session_start_time,
                    session_end_time,
                    last_speed_change_time,
                    relative_position,
                )
            elif source_type == BOX_PLAY_STATE_VOD:
                titleId = state_source["titleId"]
                last_speed_change_time = playerState["lastSpeedChangeTime"]
                relative_position = playerState["relativePosition"]
                raw_vod = self._do_api_call(
                    f"{self._config['vodService']['URL']}/v2/detailscreen/{titleId}?language={self._country_settings['language']}&profileId=4504e28d-c1cb-4284-810b-f5eaab06f034&cityId={self.customer.cityId}"
                )
                vod = LGHorizonVod(raw_vod)
                self.settop_boxes[deviceId].update_with_vod(
                    source_type, vod, last_speed_change_time, relative_position
                )
        elif uiStatus == "apps":
            app = LGHorizonApp(statusPayload["appsState"])
            self.settop_boxes[deviceId].update_with_app("app", app)

    @backoff.on_exception(
        backoff.expo, LGHorizonApiConnectionError, max_tries=3, logger=_logger
    )
    def _do_api_call(self, url: str, tries: int = 0) -> str:
        _logger.info(f"Executing API call to {url}")
        try:
            api_response = self._session.get(url)
            api_response.raise_for_status()
            json_response = api_response.json()
        except request_exceptions.HTTPError as httpEx:
            self._authorize()
            raise LGHorizonApiConnectionError(
                f"Unable to call {url}. Error:{str(httpEx)}"
            )
        _logger.debug(f"Result API call: {json_response}")
        return json_response

    def _register_customer_and_boxes(self):
        _logger.info("Get personalisation info...")
        personalisation_result = self._do_api_call(
            f"{self._config['personalizationService']['URL']}/v1/customer/{self._auth.householdId}?with=profiles%2Cdevices"
        )
        _logger.debug("Personalisation result: %s ", personalisation_result)
        self.customer = LGHorizonCustomer(personalisation_result)
        self._get_channels()
        if "assignedDevices" not in personalisation_result:
            _logger.warning("No boxes found.")
            return
        _logger.info("Registering boxes")
        for device in self.customer.settop_boxes:
            platform_type = device["platformType"]
            if platform_type not in _supported_platforms:
                continue
            if (
                "platform_types" in self._country_settings
                and platform_type in self._country_settings["platform_types"]
            ):
                platform_type = self._country_settings["platform_types"][platform_type]
            else:
                platform_type = None
            box = LGHorizonBox(
                device, platform_type, self._mqttClient, self._auth, self._channels
            )
            self.settop_boxes[box.deviceId] = box
            _logger.info("Box %s registered...", box.deviceId)

    def _get_channels(self):
        self._update_entitlements()
        _logger.info("Retrieving channels...")
        channels_result = self._do_api_call(
            f"{self._config['linearService']['URL']}/v2/channels?cityId={self.customer.cityId}&language={self._country_settings['language']}&productClass=Orion-DASH"
        )
        profile_channels = []
        if self._profile_id and self._profile_id in self.customer.profiles:
            profile_channels = self.customer.profiles[
                self._profile_id
            ].favorite_channels

        has_profile_channels = len(profile_channels) > 0
        for channel in channels_result:
            if "isRadio" in channel and channel["isRadio"]:
                continue
            common_entitlements = list(
                set(self._entitlements) & set(channel["linearProducts"])
            )
            if len(common_entitlements) == 0:
                continue
            channel_id = channel["id"]
            if has_profile_channels and channel_id not in profile_channels:
                continue

            self._channels[channel_id] = LGHorizonChannel(channel)
        _logger.info(f"{len(self._channels)} retrieved.")

    def _get_replay_event(self, listingId) -> Any:
        """Get listing."""
        _logger.info("Retrieving replay event details...")
        response = self._do_api_call(
            f"{self._config['linearService']['URL']}/v2/replayEvent/{listingId}?returnLinearContent=true&language={self._country_settings['language']}"
        )
        _logger.info("Replay event details retrieved")
        return response

    def get_recording_capacity(self) -> int:
        """Returns remaining recording capacity"""
        ctry_code = self._country_code[0:2]
        if ctry_code == "gb":
            _logger.debug("GB: not supported")
            return None
        try:
            _logger.info("Retrieving recordingcapacity...")
            quota_content = self._do_api_call(
                f"{self._config['recordingService']['URL']}/customers/{self._auth.householdId}/quota"
            )
            if not "quota" in quota_content and not "occupied" in quota_content:
                _logger.error("Unable to fetch recording capacity...")
                return None
            capacity = (quota_content["occupied"] / quota_content["quota"]) * 100
            self.recording_capacity = round(capacity)
            _logger.debug(f"Remaining recordingcapacity {self.recording_capacity}%")
            return self.recording_capacity
        except:
            _logger.error("Unable to fetch recording capacity...")
            return None

    def get_recordings(self) -> List[LGHorizonBaseRecording]:
        _logger.info("Retrieving recordings...")
        recording_content = self._do_api_call(
            f"{self._config['recordingService']['URL']}/customers/{self._auth.householdId}/recordings?sort=time&sortOrder=desc&language={self._country_settings['language']}"
        )
        recordings = []
        for recording_data_item in recording_content["data"]:
            type = recording_data_item["type"]
            if type == RECORDING_TYPE_SINGLE:
                recordings.append(LGHorizonRecordingSingle(recording_data_item))
            elif type in (RECORDING_TYPE_SEASON, RECORDING_TYPE_SHOW):
                recordings.append(LGHorizonRecordingListSeasonShow(recording_data_item))
        _logger.info(f"{len(recordings)} recordings retrieved...")
        return recordings

    def get_recording_show(self, showId: str) -> list[LGHorizonRecordingSingle]:
        _logger.info("Retrieving show recordings...")
        show_recording_content = self._do_api_call(
            f"{self._config['recordingService']['URL']}/customers/{self._auth.householdId}/episodes/shows/{showId}?source=recording&language=nl&sort=time&sortOrder=asc"
        )
        recordings = []
        for item in show_recording_content["data"]:
            if item["source"] == "show":
                recordings.append(LGHorizonRecordingShow(item))
            else:
                recordings.append(LGHorizonRecordingEpisode(item))
        _logger.info(f"{len(recordings)} showrecordings retrieved...")
        return recordings

    def _update_entitlements(self) -> None:
        _logger.info("Retrieving entitlements...")
        entitlements_json = self._do_api_call(
            f"{self._config['purchaseService']['URL']}/v2/customers/{self._auth.householdId}/entitlements?enableDaypass=true"
        )
        self._entitlements.clear()
        for entitlement in entitlements_json["entitlements"]:
            self._entitlements.append(entitlement["id"])

    def _get_config(self, country_code: str):
        ctryCode = country_code[0:2]
        config_url = f"{self._country_settings['api_url']}/{ctryCode}/en/config-service/conf/web/backoffice.json"
        result = self._do_api_call(config_url)
        _logger.debug(result)
        return result
