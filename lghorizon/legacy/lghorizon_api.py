"""Python client for LGHorizon."""
# pylint: disable=broad-exception-caught
# pylint: disable=line-too-long

import logging
import json
import re

from typing import Any, Callable, Dict, List
import backoff

from requests import Session, exceptions as request_exceptions

from .exceptions import (
    LGHorizonApiUnauthorizedError,
    LGHorizonApiConnectionError,
    LGHorizonApiLockedError,
)

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


_logger = logging.getLogger(__name__)
_supported_platforms = ["EOS", "EOS2", "HORIZON", "APOLLO"]


class LGHorizonApi:
    """Main class for handling connections with LGHorizon Settop boxes."""

    _auth: LGHorizonAuth = None
    _session: Session = None
    settop_boxes: Dict[str, LGHorizonBox] = None
    customer: LGHorizonCustomer = None
    _mqtt_client: LGHorizonMqttClient = None
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
        if ctry_code in ("gb", "ch", "be"):
            self._authorize_with_refresh_token()
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

    def _authorize_with_refresh_token(self) -> None:
        """Handle authorizzationg using request token."""
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
        self.refresh_token = self._auth.refresh_token
        self._session.cookies["ACCESSTOKEN"] = self._auth.access_token

        if self._refresh_callback:
            self._refresh_callback()

        _logger.debug("Authorization succeeded")

    def set_callback(self, refresh_callback: Callable) -> None:
        """Set the refresh callback."""
        self._refresh_callback = refresh_callback

    def _obtain_mqtt_token(self):
        _logger.debug("Obtain mqtt token...")
        mqtt_auth_url = self._config["authorizationService"]["URL"]
        mqtt_response = self._do_api_call(f"{mqtt_auth_url}/v1/mqtt/token")
        self._auth.mqttToken = mqtt_response["token"]
        _logger.debug("MQTT token: %s", self._auth.mqttToken)

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
        """Start connection process."""
        self._config = self._get_config(self._country_code)
        _logger.debug("Connect to API")
        self._authorize()
        self._obtain_mqtt_token()
        self._mqtt_client = LGHorizonMqttClient(
            self._auth,
            self._config["mqttBroker"]["URL"],
            self._on_mqtt_connected,
            self._on_mqtt_message,
        )

        self._register_customer_and_boxes()
        self._mqtt_client.connect()

    def disconnect(self):
        """Disconnect."""
        _logger.debug("Disconnect from API")
        if not self._mqtt_client or not self._mqtt_client.is_connected:
            return
        self._mqtt_client.disconnect()

    def _on_mqtt_connected(self) -> None:
        _logger.debug("Connected to MQTT server. Registering all boxes...")
        box: LGHorizonBox
        for box in self.settop_boxes.values():
            box.register_mqtt()

    def _on_mqtt_message(self, message: str, topic: str) -> None:
        if "action" in message and message["action"] == "OPS.getProfilesUpdate":
            self._update_customer()
        elif "source" in message:
            device_id = message["source"]
            if not isinstance(device_id, str):
                _logger.debug("ignoring message - not a string")
                return
            if device_id not in self.settop_boxes:
                return
            try:
                if "deviceType" in message and message["deviceType"] == "STB":
                    self.settop_boxes[device_id].update_state(message)
                if "status" in message:
                    self._handle_box_update(device_id, message)

            except Exception:
                _logger.exception("Could not handle status message")
                _logger.warning("Full message: %s", str(message))
                self.settop_boxes[device_id].playing_info.reset()
                self.settop_boxes[device_id].playing_info.set_paused(False)
        elif "CPE.capacity" in message:
            splitted_topic = topic.split("/")
            if len(splitted_topic) != 4:
                return
            device_id = splitted_topic[1]
            if device_id not in self.settop_boxes:
                return
            self.settop_boxes[device_id].update_recording_capacity(message)

    def _handle_box_update(self, device_id: str, raw_message: Any) -> None:
        status_payload = raw_message["status"]
        if "uiStatus" not in status_payload:
            return
        ui_status = status_payload["uiStatus"]
        if ui_status == "mainUI":
            player_state = status_payload["playerState"]
            if "sourceType" not in player_state or "source" not in player_state:
                return
            source_type = player_state["sourceType"]
            state_source = player_state["source"]
            self.settop_boxes[device_id].playing_info.set_paused(
                player_state["speed"] == 0
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
                event_id = state_source["eventId"]
                raw_replay_event = self._do_api_call(
                    f"{self._config['linearService']['URL']}/v2/replayEvent/{event_id}?returnLinearContent=true&language={self._country_settings['language']}"
                )
                replay_event = LGHorizonReplayEvent(raw_replay_event)
                channel = self._channels[replay_event.channel_id]
                self.settop_boxes[device_id].update_with_replay_event(
                    source_type, replay_event, channel
                )
            elif source_type == BOX_PLAY_STATE_DVR:
                recording_id = state_source["recordingId"]
                session_start_time = state_source["sessionStartTime"]
                session_end_time = state_source["sessionEndTime"]
                last_speed_change_time = player_state["lastSpeedChangeTime"]
                relative_position = player_state["relativePosition"]
                raw_recording = self._do_api_call(
                    f"{self._config['recordingService']['URL']}/customers/{self._auth.household_id}/details/single/{recording_id}?profileId=4504e28d-c1cb-4284-810b-f5eaab06f034&language={self._country_settings['language']}"
                )
                recording = LGHorizonRecordingSingle(raw_recording)
                channel = self._channels[recording.channel_id]
                self.settop_boxes[device_id].update_with_recording(
                    source_type,
                    recording,
                    channel,
                    session_start_time,
                    session_end_time,
                    last_speed_change_time,
                    relative_position,
                )
            elif source_type == BOX_PLAY_STATE_VOD:
                title_id = state_source["titleId"]
                last_speed_change_time = player_state["lastSpeedChangeTime"]
                relative_position = player_state["relativePosition"]
                raw_vod = self._do_api_call(
                    f"{self._config['vodService']['URL']}/v2/detailscreen/{title_id}?language={self._country_settings['language']}&profileId=4504e28d-c1cb-4284-810b-f5eaab06f034&cityId={self.customer.city_id}"
                )
                vod = LGHorizonVod(raw_vod)
                self.settop_boxes[device_id].update_with_vod(
                    source_type, vod, last_speed_change_time, relative_position
                )
        elif ui_status == "apps":
            app = LGHorizonApp(status_payload["appsState"])
            self.settop_boxes[device_id].update_with_app("app", app)

    @backoff.on_exception(
        backoff.expo, LGHorizonApiConnectionError, max_tries=3, logger=_logger
    )
    def _do_api_call(self, url: str) -> str:
        _logger.info("Executing API call to %s", url)
        try:
            api_response = self._session.get(url)
            api_response.raise_for_status()
            json_response = api_response.json()
        except request_exceptions.HTTPError as http_ex:
            self._authorize()
            raise LGHorizonApiConnectionError(
                f"Unable to call {url}. Error:{str(http_ex)}"
            ) from http_ex
        _logger.debug("Result API call: %s", json_response)
        return json_response

    def _register_customer_and_boxes(self):
        self._update_customer()
        self._get_channels()
        if len(self.customer.settop_boxes) == 0:
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
                device, platform_type, self._mqtt_client, self._auth, self._channels
            )
            self.settop_boxes[box.device_id] = box
            _logger.info("Box %s registered...", box.device_id)

    def _update_customer(self):
        _logger.info("Get customer data")
        personalisation_result = self._do_api_call(
            f"{self._config['personalizationService']['URL']}/v1/customer/{self._auth.household_id}?with=profiles%2Cdevices"
        )
        _logger.debug("Personalisation result: %s ", personalisation_result)
        self.customer = LGHorizonCustomer(personalisation_result)

    def _get_channels(self):
        self._update_entitlements()
        _logger.info("Retrieving channels...")
        channels_result = self._do_api_call(
            f"{self._config['linearService']['URL']}/v2/channels?cityId={self.customer.city_id}&language={self._country_settings['language']}&productClass=Orion-DASH"
        )
        for channel in channels_result:
            if "isRadio" in channel and channel["isRadio"]:
                continue
            common_entitlements = list(
                set(self._entitlements) & set(channel["linearProducts"])
            )
            if len(common_entitlements) == 0:
                continue
            channel_id = channel["id"]
            self._channels[channel_id] = LGHorizonChannel(channel)
        _logger.info("%s retrieved.", len(self._channels))

    def get_display_channels(self):
        """Returns channels to display baed on profile."""
        all_channels = self._channels.values()
        if not self._profile_id or self._profile_id not in self.customer.profiles:
            return all_channels
        profile_channel_ids = self.customer.profiles[self._profile_id].favorite_channels
        if len(profile_channel_ids) == 0:
            return all_channels

        return [
            channel for channel in all_channels if channel.id in profile_channel_ids
        ]

    def _get_replay_event(self, listing_id) -> Any:
        """Get listing."""
        _logger.info("Retrieving replay event details...")
        response = self._do_api_call(
            f"{self._config['linearService']['URL']}/v2/replayEvent/{listing_id}?returnLinearContent=true&language={self._country_settings['language']}"
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
                f"{self._config['recordingService']['URL']}/customers/{self._auth.household_id}/quota"
            )
            if "quota" not in quota_content and "occupied" not in quota_content:
                _logger.error("Unable to fetch recording capacity...")
                return None
            capacity = (quota_content["occupied"] / quota_content["quota"]) * 100
            self.recording_capacity = round(capacity)
            _logger.debug("Remaining recordingcapacity %s %%", self.recording_capacity)
            return self.recording_capacity
        except Exception:
            _logger.error("Unable to fetch recording capacity...")
            return None

    def get_recordings(self) -> List[LGHorizonBaseRecording]:
        """Returns recordings."""
        _logger.info("Retrieving recordings...")
        recording_content = self._do_api_call(
            f"{self._config['recordingService']['URL']}/customers/{self._auth.household_id}/recordings?sort=time&sortOrder=desc&language={self._country_settings['language']}"
        )
        recordings = []
        for recording_data_item in recording_content["data"]:
            recording_type = recording_data_item["type"]
            if recording_type == RECORDING_TYPE_SINGLE:
                recordings.append(LGHorizonRecordingSingle(recording_data_item))
            elif recording_type in (RECORDING_TYPE_SEASON, RECORDING_TYPE_SHOW):
                recordings.append(LGHorizonRecordingListSeasonShow(recording_data_item))
        _logger.info("%s recordings retrieved...", len(recordings))
        return recordings

    def get_recording_show(self, show_id: str) -> list[LGHorizonRecordingSingle]:
        """Returns show recording"""
        _logger.info("Retrieving show recordings...")
        show_recording_content = self._do_api_call(
            f"{self._config['recordingService']['URL']}/customers/{self._auth.household_id}/episodes/shows/{show_id}?source=recording&language=nl&sort=time&sortOrder=asc"
        )
        recordings = []
        for item in show_recording_content["data"]:
            if item["source"] == "show":
                recordings.append(LGHorizonRecordingShow(item))
            else:
                recordings.append(LGHorizonRecordingEpisode(item))
        _logger.info("%s showrecordings retrieved...", len(recordings))
        return recordings

    def _update_entitlements(self) -> None:
        _logger.info("Retrieving entitlements...")
        entitlements_json = self._do_api_call(
            f"{self._config['purchaseService']['URL']}/v2/customers/{self._auth.household_id}/entitlements?enableDaypass=true"
        )
        self._entitlements.clear()
        for entitlement in entitlements_json["entitlements"]:
            self._entitlements.append(entitlement["id"])

    def _get_config(self, country_code: str):
        base_country_code = country_code[0:2]
        config_url = f"{self._country_settings['api_url']}/{base_country_code}/en/config-service/conf/web/backoffice.json"
        result = self._do_api_call(config_url)
        _logger.debug(result)
        return result
