"""LG Horizon Model."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

import backoff
from aiohttp import ClientResponseError, ClientSession

from .const import (
    COUNTRY_SETTINGS,
)
from .exceptions import LGHorizonApiConnectionError, LGHorizonApiUnauthorizedError


_LOGGER = logging.getLogger(__name__)


def _redact_sensitive(data):
    """Redact sensitive fields from data before logging."""
    if not isinstance(data, dict):
        return data
    redacted = dict(data)
    for key in ("accessToken", "access_token", "refreshToken", "refresh_token", "token", "password"):
        if key in redacted:
            redacted[key] = "***REDACTED***"
    return redacted


class LGHorizonRunningState(Enum):
    """Running state of horizon box."""

    UNKNOWN = "UNKNOWN"
    ONLINE_RUNNING = "ONLINE_RUNNING"
    ONLINE_STANDBY = "ONLINE_STANDBY"
    OFFLINE_NETWORK_STANDBY = "OFFLINE_NETWORK_STANDBY"
    OFFLINE = "OFFLINE"


class LGHorizonMessageType(Enum):
    """Enumeration of LG Horizon message types."""

    UNKNOWN = 0
    STATUS = 1
    UI_STATUS = 2


class LGHorizonRecordingSource(Enum):
    """LGHorizon recording."""

    SHOW = "show"
    SINGLE = "single"
    SEASON = "season"
    UNKNOWN = "unknown"


class LGHorizonRecordingState(Enum):
    """Enumeration of LG Horizon recording states."""

    RECORDED = "recorded"
    ONGOING = "ongoing"
    UNKNOWN = "unknown"


class LGHorizonRecordingType(Enum):  # type: ignore[no-redef]
    """Enumeration of LG Horizon recording states."""

    SINGLE = "single"
    SEASON = "season"
    SHOW = "show"
    UNKNOWN = "unknown"


class LGHorizonUIStateType(Enum):
    """Enumeration of LG Horizon UI State types."""

    MAINUI = "mainUI"
    APPS = "apps"
    UNKNOWN = "unknown"


class LGHorizonMediaType(Enum):
    """Enumeration of LG Horizon Media types"""

    UNKNOWN = "unknown"
    CHANNEL = "channel"
    APP = "app"
    MOVIE = "movie"
    EPISODE = "episode"
    TVSHOW = "tvshow"


class LGHorizonMessage(ABC):
    """Abstract base class for LG Horizon messages."""

    @property
    def topic(self) -> str:
        """Return the topic of the message."""
        return self._topic

    @property
    def payload(self) -> dict:
        """Return the payload of the message."""
        return self._payload

    @property
    @abstractmethod
    def message_type(self) -> LGHorizonMessageType | None:
        """Return the message type."""

    @abstractmethod
    def __init__(self, topic: str, payload: dict) -> None:
        """Initialize the abstract base class for LG Horizon messages.

        Args:
            topic: The MQTT topic of the message.
            payload: The dictionary payload of the message.
        """
        self._topic = topic
        self._payload = payload

    def __repr__(self) -> str:
        """Return a string representation of the message."""
        return f"LGHorizonStatusMessage(topic='{self._topic}', payload={json.dumps(self._payload, indent=2)})"


class LGHorizonStatusMessage(LGHorizonMessage):
    """Represents an LG Horizon status message received via MQTT."""

    def __init__(self, payload: dict, topic: str) -> None:
        """Initialize an LG Horizon status message."""
        super().__init__(topic, payload)

    @property
    def message_type(self) -> LGHorizonMessageType:
        """Return the message type from the payload, if available."""
        return LGHorizonMessageType.STATUS

    @property
    def source(self) -> str:
        """Return the device ID from the payload, if available."""
        return self._payload.get("source", "unknown")

    @property
    def running_state(self) -> LGHorizonRunningState:
        """Return the running state from the payload."""
        state_str = self._payload.get("state", "unknown").upper()
        try:
            return LGHorizonRunningState[state_str]
        except KeyError:
            return LGHorizonRunningState.UNKNOWN


class LGHorizonSourceType(Enum):
    """Enumeration of LG Horizon source types."""

    LINEAR = "linear"
    REVIEWBUFFER = "reviewBuffer"
    NDVR = "nDVR"
    LOCALDVR = "localDVR"
    REPLAY = "replay"
    VOD = "VOD"
    UNKNOWN = "unknown"


class LGHorizonSource(ABC):
    """Abstract base class for LG Horizon sources."""

    def __init__(self, raw_json: dict) -> None:
        """Initialize the LG Horizon source."""
        self._raw_json = raw_json

    @property
    @abstractmethod
    def source_type(self) -> LGHorizonSourceType:  # type: ignore[no-redef]
        """Return the message type."""


class LGHorizonLinearSource(LGHorizonSource):
    """Represent the Linear Source of an LG Horizon device."""

    @property
    def channel_id(self) -> str:
        """Return the channel ID."""
        return self._raw_json.get("channelId", "")

    @property
    def event_id(self) -> str:
        """Return the event ID."""
        return self._raw_json.get("eventId", "")

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.LINEAR


class LGHorizonReviewBufferSource(LGHorizonSource):
    """Represent the ReviewBuffer Source of an LG Horizon device."""

    @property
    def channel_id(self) -> str:
        """Return the channel ID."""
        return self._raw_json.get("channelId", "")

    @property
    def event_id(self) -> str:
        """Return the event ID."""
        return self._raw_json.get("eventId", "")

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.REVIEWBUFFER


class LGHorizonNDVRSource(LGHorizonSource):
    """Represent the Network Digital Video Recorder (NDVR) Source of an LG Horizon device."""

    @property
    def recording_id(self) -> str:
        """Return the recording ID."""
        return self._raw_json.get("recordingId", "")

    @property
    def channel_id(self) -> str:
        """Return the channel ID."""
        return self._raw_json.get("channelId", "")

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.NDVR


class LGHorizonVODSource(LGHorizonSource):
    """Represent the VOD Source of an LG Horizon device."""

    @property
    def title_id(self) -> str:
        """Return the title ID."""
        return self._raw_json.get("titleId", "")

    @property
    def start_intro_time(self) -> int:
        """Return the start intro time."""
        return self._raw_json.get("startIntroTime", 0)

    @property
    def end_intro_time(self) -> int:
        """Return the end intro time."""
        return self._raw_json.get("endIntroTime", 0)

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.VOD


class LGHorizonReplaySource(LGHorizonSource):
    """Represent the Replay Source of an LG Horizon device."""

    @property
    def event_id(self) -> str:
        """Return the event ID."""
        return self._raw_json.get("eventId", "")

    @property
    def source_type(self) -> LGHorizonSourceType:
        """Return the source type."""
        return LGHorizonSourceType.REPLAY


class LGHorizonUnknownSource(LGHorizonSource):
    """Represent an unknown source type of an LG Horizon device."""

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.UNKNOWN


class LGHorizonPlayerState:
    """Represent the Player State of an LG Horizon device."""

    def __init__(self, raw_json: dict) -> None:
        """Initialize the Player State."""
        self._raw_json = raw_json

    @property
    def source_type(self) -> LGHorizonSourceType:
        """Return the source type."""
        type_str = self._raw_json.get("sourceType", "unknown").upper()
        try:
            return LGHorizonSourceType[type_str]
        except KeyError:
            return LGHorizonSourceType.UNKNOWN

    @property
    def speed(self) -> int:
        """Return the playback speed."""
        return self._raw_json.get("speed", 0)

    @property
    def last_speed_change_time(
        self,
    ) -> Optional[float]:
        """Return the last speed change time."""
        val = self._raw_json.get("lastSpeedChangeTime")
        return val / 1000 if val is not None else None

    @property
    def relative_position(
        self,
    ) -> int:
        """Return the relative position."""
        return self._raw_json.get("relativePosition", 0.0)

    @property
    def source(self) -> LGHorizonSource | None:  # Added None to the return type
        """Return the source."""
        if "source" in self._raw_json:
            match self.source_type:
                case LGHorizonSourceType.LINEAR:
                    return LGHorizonLinearSource(self._raw_json["source"])
                case LGHorizonSourceType.VOD:
                    return LGHorizonVODSource(self._raw_json["source"])
                case LGHorizonSourceType.REPLAY:
                    return LGHorizonReplaySource(self._raw_json["source"])
                case LGHorizonSourceType.NDVR:
                    return LGHorizonNDVRSource(self._raw_json["source"])
                case LGHorizonSourceType.REVIEWBUFFER:
                    return LGHorizonReviewBufferSource(self._raw_json["source"])

        return None


class LGHorizonAppsState:
    """Represent the Apps State of an LG Horizon device."""

    def __init__(self, raw_json: dict) -> None:
        """Initialize the Apps state."""
        self._raw_json = raw_json

    @property
    def id(self) -> str:
        """Return the id."""
        return self._raw_json.get("id", "")

    @property
    def app_name(self) -> str:
        """Return the app name."""
        return self._raw_json.get("appName", "")

    @property
    def logo_path(self) -> str:
        """Return the logo path."""
        return self._raw_json.get("logoPath", "")


class LGHorizonUIState:
    """Represent the UI State of an LG Horizon device."""

    _player_state: LGHorizonPlayerState | None = None
    _apps_state: LGHorizonAppsState | None = None

    def __init__(self, raw_json: dict) -> None:
        """Initialize the UI State.

        Args:
            raw_json: The raw JSON dictionary containing UI state information.
        """
        self._raw_json = raw_json

    @property
    def ui_status(self) -> LGHorizonUIStateType:
        """Return the UI status type."""
        status_str = self._raw_json.get("uiStatus", "unknown").upper()
        try:
            return LGHorizonUIStateType[status_str]
        except KeyError:
            return LGHorizonUIStateType.UNKNOWN

    @property
    def player_state(
        self,
    ) -> LGHorizonPlayerState | None:  # Added None to the return type
        """Return the player state."""
        # Check if _player_state is None and if "playerState" key exists in raw_json
        if self._player_state is None and "playerState" in self._raw_json:
            self._player_state = LGHorizonPlayerState(
                self._raw_json["playerState"]
            )  # Access directly as existence is checked
        return self._player_state

    @property
    def apps_state(
        self,
    ) -> LGHorizonAppsState | None:  # Added None to the return type
        """Return the apps state."""
        # Check if _player_state is None and if "playerState" key exists in raw_json
        if self._apps_state is None and "appsState" in self._raw_json:
            self._apps_state = LGHorizonAppsState(
                self._raw_json["appsState"]
            )  # Access directly as existence is checked
        return self._apps_state


class LGHorizonUIStatusMessage(LGHorizonMessage):
    """Represents an LG Horizon UI status message received via MQTT."""

    _status: LGHorizonUIState | None = None

    def __init__(self, payload: dict, topic: str) -> None:
        """Initialize an LG Horizon UI status message."""
        super().__init__(topic, payload)

    @property
    def message_type(self) -> LGHorizonMessageType:
        """Return the message type from the payload, if available."""
        return LGHorizonMessageType.UI_STATUS

    @property
    def source(self) -> str:
        """Return the device ID from the payload, if available."""
        return self._payload.get("source", "unknown")

    @property
    def message_timestamp(self) -> float:
        """Return the message timestamp from the payload."""
        val = self._payload.get("messageTimeStamp", 0)
        return val / 1000 if val else 0

    @property
    def ui_state(self) -> LGHorizonUIState | None:
        """Return the UI state from the payload."""
        if not self._status and "status" in self._payload:
            self._status = LGHorizonUIState(self._payload["status"])
        return self._status


class LGHorizonUnknownMessage(LGHorizonMessage):
    """Represents an unknown LG Horizon message received via MQTT."""

    def __init__(self, payload: dict, topic: str) -> None:
        """Initialize an LG Horizon unknown message."""
        super().__init__(topic, payload)

    @property
    def message_type(self) -> LGHorizonMessageType:
        """Return the message type from the payload, if available."""
        return LGHorizonMessageType.UNKNOWN


class LGHorizonProfileOptions:
    """LGHorizon profile options."""

    def __init__(self, options_payload: dict):
        """Initialize a profile options."""
        self._options_payload = options_payload

    @property
    def lang(self) -> str:
        """Return the language."""
        return self._options_payload["lang"]


class LGHorizonProfile:
    """LGHorizon profile."""

    _options: LGHorizonProfileOptions
    _profile_payload: dict

    def __init__(self, profile_payload: dict):
        """Initialize a profile."""
        self._profile_payload = profile_payload
        self._options = LGHorizonProfileOptions(self._profile_payload["options"])

    @property
    def id(self) -> str:
        """Return the profile id."""
        return self._profile_payload["profileId"]

    @property
    def name(self) -> str:
        """Return the profile name."""
        return self._profile_payload["name"]

    @property
    def favorite_channels(self) -> list[str]:
        """Return the favorite channels."""
        return self._profile_payload.get("favoriteChannels", [])

    @property
    def options(self) -> LGHorizonProfileOptions:
        """Return the profile options."""
        return self._options


class LGHorizonAuth:
    """Class to make authenticated requests."""

    _websession: ClientSession
    _refresh_token: str
    _access_token: Optional[str]
    _username: str
    _password: str
    _household_id: str
    _token_expiry: Optional[int]
    _country_code: str
    _host: str
    _use_refresh_token: bool
    _token_refresh_callback: Callable[[str], None] | None

    def __init__(
        self,
        websession: ClientSession,
        country_code: str,
        refresh_token: str = "",
        username: str = "",
        password: str = "",
        token_refresh_callback: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize the auth with refresh token."""
        self._websession = websession
        self._refresh_token = refresh_token
        self._access_token = None
        self._username = username
        self._password = password
        self._household_id = ""
        self._token_expiry = None
        self._country_code = country_code
        self._host = COUNTRY_SETTINGS[country_code]["api_url"]
        self._use_refresh_token = COUNTRY_SETTINGS[country_code]["use_refreshtoken"]
        self._service_config = None
        self._token_refresh_callback = token_refresh_callback

    @property
    def websession(self) -> ClientSession:
        """Return the aiohttp client session."""
        return self._websession

    @property
    def refresh_token(self) -> str:
        """Return the refresh token."""
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: str) -> None:
        """Set the refresh token."""
        self._refresh_token = value

    @property
    def access_token(self) -> Optional[str]:
        """Return the access token."""
        return self._access_token

    @access_token.setter
    def access_token(self, value: Optional[str]) -> None:
        """Set the access token."""
        self._access_token = value

    @property
    def username(self) -> str:
        """Return the username."""
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        """Set the username."""
        self._username = value

    @property
    def password(self) -> str:
        """Return the password."""
        return self._password

    @password.setter
    def password(self, value: str) -> None:
        """Set the password."""
        self._password = value

    @property
    def household_id(self) -> str:
        """Return the household ID."""
        return self._household_id

    @household_id.setter
    def household_id(self, value: str) -> None:
        """Set the household ID."""
        self._household_id = value

    @property
    def token_expiry(self) -> Optional[int]:
        """Return the token expiry timestamp."""
        return self._token_expiry

    @token_expiry.setter
    def token_expiry(self, value: Optional[int]) -> None:
        """Set the token expiry timestamp."""
        self._token_expiry = value

    @property
    def country_code(self) -> str:
        """Return the country code."""
        return self._country_code

    def is_token_expiring(self) -> bool:
        """Check if the token is expiring within one day."""
        if not self.access_token or not self.token_expiry:
            return True
        current_unix_time = int(time.time())
        return current_unix_time >= (self.token_expiry - 86400)

    async def fetch_access_token(self) -> None:
        """Fetch the access token."""
        _LOGGER.debug("Fetching access token")
        headers = dict()
        headers["content-type"] = "application/json"
        headers["charset"] = "utf-8"

        if not self._use_refresh_token and self.access_token is None:
            payload = {"password": self.password, "username": self.username}
            headers["x-device-code"] = "web"
            auth_url_path = "/auth-service/v1/authorization"
        else:
            payload = {"refreshToken": self.refresh_token}
            auth_url_path = "/auth-service/v1/authorization/refresh"
        try:  # Use properties and backing fields
            auth_response = await self.websession.post(
                f"{self._host}{auth_url_path}",
                json=payload,
                headers=headers,
            )
        except Exception as ex:
            raise LGHorizonApiConnectionError from ex
        auth_json = await auth_response.json()
        if not auth_response.ok:
            error = None
            if "error" in auth_json:
                error = auth_json["error"]
            if error and error["statusCode"] == 97401:
                raise LGHorizonApiUnauthorizedError("Invalid credentials")
            elif error and error["statusCode"] == 97402:
                raise LGHorizonApiUnauthorizedError("Invalid token")
            elif error:
                raise LGHorizonApiConnectionError(error["message"])
            else:
                raise LGHorizonApiConnectionError("Unknown connection error")

        self.household_id = auth_json["householdId"]
        self.access_token = auth_json["accessToken"]
        self.refresh_token = auth_json["refreshToken"]
        if self._token_refresh_callback:
            self._token_refresh_callback(self.refresh_token)
        self.username = auth_json["username"]
        self.token_expiry = auth_json["refreshTokenExpiry"]
        _LOGGER.debug(
            "Access token and refresh token fetched. refresh token expires: %s",
            datetime.fromtimestamp(int(self.token_expiry)).ctime(),
        )

    @backoff.on_exception(backoff.expo, LGHorizonApiConnectionError, max_tries=3)
    async def request(self, host: str, path: str, params=None, **kwargs) -> Any:
        """Make a request."""
        if headers := kwargs.pop("headers", {}):
            headers = dict(headers)
        request_url = f"{host}{path}"
        if self.is_token_expiring():  # Use property
            _LOGGER.debug("Access token is expiring, fetching a new one")
            await self.fetch_access_token()
        try:
            web_response = await self.websession.request(
                "GET", request_url, **kwargs, headers=headers, params=params
            )
            web_response.raise_for_status()
            json_response = await web_response.json()
            _LOGGER.debug(
                "Response from %s:\n %s",
                request_url,
                json.dumps(_redact_sensitive(json_response), indent=2),
            )
            return json_response
        except ClientResponseError as cre:
            _LOGGER.error("Error response from %s: %s", request_url, str(cre))
            if cre.status == 401:
                await self.fetch_access_token()
            raise LGHorizonApiConnectionError(
                f"Unable to call {request_url}. Error:{str(cre)}"
            ) from cre

        except Exception as ex:
            _LOGGER.error("Error calling %s: %s", request_url, str(ex))
            raise LGHorizonApiConnectionError(
                f"Unable to call {request_url}. Error:{str(ex)}"
            ) from ex

    async def get_mqtt_token(self) -> Any:
        """Get the MQTT token."""
        _LOGGER.debug("Fetching MQTT token")
        config = await self.get_service_config()
        service_url = config.get_service_url("authorizationService")
        result = await self.request(
            service_url,
            "/v1/mqtt/token",
        )
        return result["token"]

    async def get_service_config(self):
        """Get the service configuration."""
        _LOGGER.debug("Fetching service configuration")
        if self._service_config is None:  # Use property and backing field
            base_country_code = self.country_code[0:2]
            result = await self.request(
                self._host,
                f"/{base_country_code}/en/config-service/conf/web/backoffice.json",
            )
            self._service_config = LGHorizonServicesConfig(result)

        return self._service_config


class LGHorizonChannel:
    """Class to represent a channel."""

    def __init__(self, channel_json):
        """Initialize a channel."""
        self.channel_json = channel_json

    @property
    def id(self) -> str:
        """Returns the id."""
        return self.channel_json["id"]

    @property
    def channel_number(self) -> str:
        """Returns the channel number."""
        return self.channel_json["logicalChannelNumber"]

    @property
    def replay_pre_padding(self) -> int:
        """Returns the replay pre-padding."""
        return self.channel_json.get("replayPrePadding", 0)

    @property
    def replay_post_padding(self) -> int:
        """Returns the replay post-padding."""
        return self.channel_json.get("replayPostPadding", 0)

    @property
    def is_radio(self) -> bool:
        """Returns if the channel is a radio channel."""
        return self.channel_json.get("isRadio", False)

    @property
    def title(self) -> str:
        """Returns the title."""
        return self.channel_json["name"]

    @property
    def logo_image(self) -> str:
        """Returns the logo image."""
        if "logo" in self.channel_json and "focused" in self.channel_json["logo"]:
            return self.channel_json["logo"]["focused"]
        return ""

    @property
    def linear_products(self) -> list[str]:
        """Returns the linear products."""
        return self.channel_json.get("linearProducts", [])

    @property
    def stream_image(self) -> str:
        """Returns the stream image."""
        image_stream = self.channel_json["imageStream"]
        if "full" in image_stream:
            return image_stream["full"]
        if "small" in image_stream:
            return image_stream["small"]
        if "logo" in self.channel_json and "focused" in self.channel_json["logo"]:
            return self.channel_json["logo"]["focused"]
        return ""


class LGHorizonServicesConfig:
    """Handle LG Horizon configuration and service URLs."""

    def __init__(self, config_data: dict[str, Any]) -> None:
        """Initialize LG Horizon config.

        Args:
            config_data: Configuration dictionary with service endpoints
        """
        self._config = config_data

    def get_service_url(self, service_name: str) -> str:
        """Get the URL for a specific service.

        Args:
            service_name: Name of the service (e.g., 'authService', 'recordingService')

        Returns:
            URL for the service

        Raises:
            ValueError: If the service or its URL is not found
        """
        if service_name in self._config and "URL" in self._config[service_name]:
            return self._config[service_name]["URL"]
        raise ValueError(f"Service URL for '{service_name}' not found in configuration")

    def get_all_services(self) -> dict[str, str]:
        """Get all available services and their URLs.

        Returns:
            Dictionary mapping service names to URLs
        """
        return {
            name: url
            for name, service in self._config.items()
            if isinstance(service, dict) and (url := service.get("URL"))
        }

    def __repr__(self) -> str:
        """Return string representation."""
        services = list(self._config.keys())
        return f"LGHorizonConfig({len(services)} services)"


class LGHorizonCustomer:
    """LGHorizon customer."""

    def __init__(self, json_payload: dict):
        """Initialize a customer."""
        self._json_payload = json_payload
        self._profiles: Dict[str, LGHorizonProfile] = {}

    @property
    def customer_id(self) -> str:
        """Return the customer id."""
        return self._json_payload["customerId"]

    @property
    def hashed_customer_id(self) -> str:
        """Return the hashed customer id."""
        return self._json_payload["hashedCustomerId"]

    @property
    def country_id(self) -> str:
        """Return the country id."""
        return self._json_payload["countryId"]

    @property
    def city_id(self) -> int:
        """Return the city id."""
        return self._json_payload["cityId"]

    @property
    def recording_retention_period(self) -> Optional[int]:
        """Return the recording retention period."""
        return self._json_payload.get("recordingRetentionPeriod", None)

    @property
    def has_cloud_recording(self) -> bool:
        """Return whether the customer has cloud recording."""
        return bool(self.recording_retention_period and self.recording_retention_period > 0)

    @property
    def assigned_devices(self) -> list[str]:
        """Return the assigned set-top boxes."""
        return self._json_payload.get("assignedDevices", [])

    @property
    def profiles(self) -> Dict[str, LGHorizonProfile]:
        """Return the profiles."""
        if not self._profiles or self._profiles == {}:
            self._profiles = {
                p["profileId"]: LGHorizonProfile(p)
                for p in self._json_payload.get("profiles", [])
            }
        return self._profiles

    def get_profile_lang(self, profile_id: str) -> str:
        """Return the profile language."""
        if profile_id not in self.profiles:
            return "nl"
        return self.profiles[profile_id].options.lang



@dataclass
class LGHorizonDeviceState:
    """Represent current state of a box."""

    state: LGHorizonRunningState = field(default_factory=lambda: LGHorizonRunningState.UNKNOWN)
    source_type: LGHorizonSourceType = field(default_factory=lambda: LGHorizonSourceType.UNKNOWN)
    ui_state_type: LGHorizonUIStateType = field(default_factory=lambda: LGHorizonUIStateType.UNKNOWN)
    media_type: LGHorizonMediaType = field(default_factory=lambda: LGHorizonMediaType.UNKNOWN)
    id: Optional[str] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    show_title: Optional[str] = None
    app_name: Optional[str] = None
    episode_title: Optional[str] = None
    episode_number: Optional[int] = None
    season_number: Optional[int] = None
    image: Optional[str] = None
    speed: Optional[int] = None
    position: Optional[float] = None
    duration: Optional[float] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    last_position_update: Optional[int] = None

    @property
    def paused(self) -> bool:
        """Return if the media is paused."""
        if self.speed is None:
            return False
        return self.speed == 0

    def reset_progress(self) -> None:
        """Reset the progress-related attributes."""
        self.position = None
        self.duration = None
        self.start_time = None
        self.end_time = None
        self.last_position_update = None

    def reset(self) -> None:
        """Reset all playing information."""
        self.id = None
        self.channel_id = None
        self.channel_name = None
        self.show_title = None
        self.app_name = None
        self.episode_title = None
        self.episode_number = None
        self.season_number = None
        self.image = None
        self.speed = None
        self.source_type = LGHorizonSourceType.UNKNOWN
        self.ui_state_type = LGHorizonUIStateType.UNKNOWN
        self.media_type = LGHorizonMediaType.UNKNOWN
        self.reset_progress()



class LGHorizonEntitlements:
    """Class to represent entitlements."""

    def __init__(self, entitlements_json):
        """Initialize entitlements."""
        self.entitlements_json = entitlements_json

    @property
    def entitlements(self):
        """Returns the entitlements."""
        return self.entitlements_json.get("entitlements", [])

    @property
    def entitlement_ids(self) -> list[str]:
        """Returns a list of entitlement IDs."""
        return [e["id"] for e in self.entitlements if "id" in e]


class LGHorizonReplayEvent:
    """LGhorizon replay event."""

    def __init__(self, raw_json: dict):
        """Initialize an LG Horizon replay event."""
        self._raw_json = raw_json

    @property
    def episode_number(self) -> Optional[int]:
        """Return the episode number."""
        return self._raw_json.get("episodeNumber")

    @property
    def channel_id(self) -> str:
        """Return the channel ID."""
        return self._raw_json["channelId"]

    @property
    def event_id(self) -> str:
        """Return the event ID."""
        return self._raw_json["eventId"]

    @property
    def season_number(self) -> Optional[int]:
        """Return the season number."""
        return self._raw_json.get("seasonNumber")

    @property
    def start_time(self) -> Optional[float]:
        """Return the start time as Unix timestamp in seconds."""
        return self._raw_json.get("startTime")

    @property
    def end_time(self) -> Optional[float]:
        """Return the end time as Unix timestamp in seconds."""
        return self._raw_json.get("endTime")

    @property
    def title(self) -> str:
        """Return the title of the event."""
        return self._raw_json["title"]

    @property
    def episode_name(self) -> Optional[str]:
        """Return the episode name."""
        return self._raw_json.get("episodeName", None)

    @property
    def full_episode_title(self) -> Optional[str]:
        """Return the full episode title."""

        if not self.season_number and not self.episode_number:
            return None
        full_title = f"""S{self.season_number:02d}E{self.episode_number:02d}"""
        if self.episode_name:
            full_title += f": {self.episode_name}"
        return full_title


class LGHorizonVODType(Enum):
    """Enumeration of LG Horizon VOD types."""

    ASSET = "ASSET"
    EPISODE = "EPISODE"
    UNKNOWN = "UNKNOWN"


class LGHorizonVOD:
    """LGHorizon video on demand."""

    def __init__(self, vod_json) -> None:
        """Initialize an LG Horizon VOD object.

        Args:
            vod_json: The raw JSON dictionary containing VOD information.
        """
        self._vod_json = vod_json

    @property
    def vod_type(self) -> LGHorizonVODType:
        """Return the type of the VOD."""
        type_str = self._vod_json.get("type", "unknown").upper()
        try:
            return LGHorizonVODType[type_str]
        except KeyError:
            return LGHorizonVODType.UNKNOWN

    @property
    def id(self) -> str:
        """Return the ID of the VOD."""
        return self._vod_json["id"]

    @property
    def season(self) -> Optional[int]:
        """Return the season number of the recording."""
        return self._vod_json.get("season", None)

    @property
    def episode(self) -> Optional[int]:
        """Return the episode number of the recording."""
        return self._vod_json.get("episode", None)

    @property
    def title(self) -> str:
        """Return the title of the VOD."""
        return self._vod_json["title"]

    @property
    def series_title(self) -> Optional[str]:
        """Return the series title of the VOD."""
        return self._vod_json.get("seriesTitle", None)

    @property
    def duration(self) -> float:
        """Return the duration of the VOD."""
        return self._vod_json["duration"]


class LGHOrizonRelevantEpisode:
    """Represents a relevant episode within a recording season or show."""

    def __init__(self, episode_json: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        self._episode_json = episode_json

    @property
    def recording_state(self) -> LGHorizonRecordingState:
        """Return the recording state."""
        state_str = self._episode_json.get("recordingState", "unknown").upper()
        try:
            return LGHorizonRecordingState[state_str]
        except KeyError:
            return LGHorizonRecordingState.UNKNOWN

    @property
    def season_number(self) -> Optional[int]:
        """Return the season number of the recording."""
        return self._episode_json.get("seasonNumber", None)

    @property
    def episode_number(self) -> Optional[int]:
        """Return the episode number of the recording."""
        return self._episode_json.get("episodeNumber", None)


class LGHorizonRecording(ABC):
    """Abstract base class for LG Horizon recordings."""

    @property
    def recording_payload(self) -> dict:
        """Return the recording payload."""
        return self._recording_payload

    @property
    def recording_state(self) -> LGHorizonRecordingState:
        """Return the recording state."""
        state_str = self._recording_payload.get("recordingState", "unknown").upper()
        try:
            return LGHorizonRecordingState[state_str]
        except KeyError:
            return LGHorizonRecordingState.UNKNOWN

    @property
    def source(self) -> LGHorizonRecordingSource:
        """Return the recording source."""
        source_str = self._recording_payload.get("source", "unknown").upper()
        try:
            return LGHorizonRecordingSource[source_str]
        except KeyError:
            return LGHorizonRecordingSource.UNKNOWN

    @property
    def type(self) -> LGHorizonRecordingType:
        """Return the recording type."""
        type_str = self._recording_payload.get("type", "unknown").upper()
        try:
            return LGHorizonRecordingType[type_str]
        except KeyError:
            return LGHorizonRecordingType.UNKNOWN

    @property
    def id(self) -> str:
        """Return the ID of the recording."""
        return self._recording_payload["id"]

    @property
    def title(self) -> str:
        """Return the title of the recording."""
        return self._recording_payload.get("title", "unknown")

    @property
    def channel_id(self) -> str:
        """Return the channel ID of the recording."""
        return self._recording_payload["channelId"]

    @property
    def poster_url(self) -> Optional[str]:
        """Return the poster URL of the recording."""
        poster = self._recording_payload.get("poster")
        if poster:
            return poster.get("url")
        return None

    def __init__(self, recording_payload: dict) -> None:
        """Abstract base class for LG Horizon recordings.
        Args:
            recording_payload: The raw JSON dictionary containing recording information.
        """
        self._recording_payload = recording_payload


class LGHorizonRecordingSingle(LGHorizonRecording):
    """LGHorizon recording."""

    @property
    def episode_title(self) -> Optional[str]:
        """Return the episode title of the recording."""
        return self._recording_payload.get("episodeTitle", None)

    @property
    def episode_id(self) -> Optional[str]:
        """Return the episode ID of the recording."""
        return self._recording_payload.get("episodeId", None)

    @property
    def season_number(self) -> Optional[int]:
        """Return the season number of the recording."""
        return self._recording_payload.get("seasonNumber", None)

    @property
    def episode_number(self) -> Optional[int]:
        """Return the episode number of the recording."""
        return self._recording_payload.get("episodeNumber", None)

    @property
    def show_id(self) -> Optional[str]:
        """Return the show ID of the recording."""
        return self._recording_payload.get("showId", None)

    @property
    def show_title(self) -> Optional[str]:
        """Return the show title of the recording."""
        return self._recording_payload.get("showTitle", None)

    @property
    def season_id(self) -> Optional[str]:
        """Return the season ID of the recording."""
        return self._recording_payload.get("seasonId", None)

    @property
    def channel_id(self) -> Optional[str]:
        """Return the channel ID of the recording."""
        return self._recording_payload.get("channelId", None)

    @property
    def duration(self) -> Optional[int]:
        """Return the duration of the recording."""
        return self.recording_payload.get("duration", None)

    @property
    def start_time(self) -> Optional[str]:
        """Return the start time as ISO-8601 string."""
        return self.recording_payload.get("startTime", None)

    @property
    def end_time(self) -> Optional[str]:
        """Return the end time as ISO-8601 string."""
        return self.recording_payload.get("endTime", None)


class LGHorizonRecordingSeason(LGHorizonRecording):
    """Represents an LG Horizon recording season."""

    _most_relevant_epsode: Optional[LGHOrizonRelevantEpisode]

    def __init__(self, payload: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        super().__init__(payload)
        episode_payload = payload.get("mostRelevantEpisode")
        if episode_payload:
            self._most_relevant_epsode = LGHOrizonRelevantEpisode(episode_payload)
        else:
            self._most_relevant_epsode = None

    @property
    def no_of_episodes(self) -> int:
        """Return the number of episodes in the season."""
        return self._recording_payload.get("noOfEpisodes", 0)

    @property
    def season_title(self) -> str:
        """Return the season title of the recording."""
        return self._recording_payload.get("seasonTitle", "")

    @property
    def show_id(self) -> str:
        """Return the show ID of the recording."""
        return self._recording_payload.get("showId", "")

    @property
    def most_relevant_episode(self) -> Optional[LGHOrizonRelevantEpisode]:
        """Return the most relevant episode of the season."""
        return self._most_relevant_epsode


class LGHorizonRecordingShow(LGHorizonRecording):
    """Represents an LG Horizon recording show."""

    _most_relevant_epsode: Optional[LGHOrizonRelevantEpisode]

    def __init__(self, payload: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        super().__init__(payload)
        episode_payload = payload.get("mostRelevantEpisode")
        if episode_payload:
            self._most_relevant_epsode = LGHOrizonRelevantEpisode(episode_payload)
        else:
            self._most_relevant_epsode = None

    @property
    def no_of_episodes(self) -> int:
        """Return the number of episodes in the season."""
        return self._recording_payload.get("noOfEpisodes", 0)

    @property
    def most_relevant_episode(self) -> Optional[LGHOrizonRelevantEpisode]:
        """Return the most relevant episode of the season."""
        return self._most_relevant_epsode


class LGHorizonRecordingList:
    """Represents a list of LG Horizon recordings."""

    @property
    def total(self) -> int:
        """Return the total number of recordings."""
        return len(self._recordings)

    def __init__(self, recordings: List[LGHorizonRecording]) -> None:
        """Initialize an LG Horizon recording list.

        Args:
            recordings: A list of LGHorizonRecording objects.
        """
        self._recordings = recordings

    @property
    def recordings(self) -> List[LGHorizonRecording]:
        """Return the list of recordings."""
        return self._recordings


class LGHorizonShowRecordingList(LGHorizonRecordingList):
    """LGHorizon recording."""

    def __init__(
        self,
        show_title: Optional[str],
        show_image,
        recordings: List[LGHorizonRecording],
    ) -> None:
        """Initialize an LG Horizon show recording list.

        Args:
            show_title: The title of the show.
            show_image: The image URL for the show.
            recordings: A list of LGHorizonRecording objects belonging to the show.
        """
        super().__init__(recordings)
        self._show_title = show_title
        self._show_image = show_image

    @property
    def show_title(self) -> str:
        """Title of the show."""
        return self._show_title

    @property
    def show_image(self) -> Optional[str]:
        """Image of the show."""
        return self._show_image


class LGHorizonRecordingQuota:
    """LGHorizon recording quota."""

    def __init__(self, quota_json: dict) -> None:
        """Initialize the recording quota."""
        self._quota_json = quota_json

    @property
    def quota(self) -> int:
        """Return the total space in MB."""
        return self._quota_json.get("quota", 0)

    @property
    def occupied(self) -> int:
        """Return the used space in MB."""
        return self._quota_json.get("occupied", 0)

    @property
    def percentage_used(self) -> float:
        """Return the percentage of space used."""
        if self.quota == 0:
            return 0.0
        return (self.occupied / self.quota) * 100


class LGHorizonEpgEvent:
    """A single EPG event (program) from the EPG service."""

    def __init__(self, event_json: dict, channel_id: str) -> None:
        """Initialize an EPG event.

        Args:
            event_json: Raw event data from the EPG segments API.
            channel_id: The channel this event belongs to.
        """
        self._event_json = event_json
        self._channel_id = channel_id

    @property
    def event_id(self) -> str:
        """Return the event ID (crid)."""
        return self._event_json.get("id", "")

    @property
    def channel_id(self) -> str:
        """Return the channel ID this event belongs to."""
        return self._channel_id

    @property
    def title(self) -> str:
        """Return the event title."""
        return self._event_json.get("title", "")

    @property
    def start_time(self) -> Optional[float]:
        """Return the start time as Unix timestamp in seconds."""
        return self._event_json.get("startTime")

    @property
    def end_time(self) -> Optional[float]:
        """Return the end time as Unix timestamp in seconds."""
        return self._event_json.get("endTime")

    @property
    def minimum_age(self) -> int:
        """Return the minimum age rating."""
        return self._event_json.get("minimumAge", 0)

    @property
    def is_placeholder(self) -> bool:
        """Return whether this is a placeholder event."""
        return self._event_json.get("isPlaceHolder", False)

    @property
    def merged_id(self) -> Optional[str]:
        """Return the merged ID."""
        return self._event_json.get("mergedId")

    @property
    def audio_languages(self) -> List[str]:
        """Return list of audio language codes."""
        langs = self._event_json.get("audioLanguages", [])
        return [item.get("lang", "") for item in langs if isinstance(item, dict)]


class LGHorizonEpgEntry:
    """EPG data for a single channel containing multiple events."""

    def __init__(self, entry_json: dict) -> None:
        """Initialize an EPG channel entry.

        Args:
            entry_json: Raw entry data from the EPG segments API.
        """
        self._entry_json = entry_json
        channel_id = entry_json.get("channelId", "")
        self._events = [
            LGHorizonEpgEvent(ev, channel_id)
            for ev in entry_json.get("events", [])
        ]

    @property
    def channel_id(self) -> str:
        """Return the channel ID."""
        return self._entry_json.get("channelId", "")

    @property
    def events(self) -> List[LGHorizonEpgEvent]:
        """Return the list of EPG events for this channel."""
        return self._events


class LGHorizonEpg:
    """Full EPG response containing entries for multiple channels."""

    def __init__(self, entries: List[LGHorizonEpgEntry]) -> None:
        """Initialize the EPG.

        Args:
            entries: List of EPG channel entries (merged from all segments).
        """
        self._entries = entries

    @property
    def entries(self) -> List[LGHorizonEpgEntry]:
        """Return all channel entries."""
        return self._entries

    def get_channel_events(self, channel_id: str) -> List[LGHorizonEpgEvent]:
        """Return EPG events for a specific channel.

        Args:
            channel_id: The channel ID to filter by.

        Returns:
            List of EPG events for the channel, or empty list if not found.
        """
        for entry in self._entries:
            if entry.channel_id == channel_id:
                return entry.events
        return []


class LGHorizonEventDetail:
    """Detailed program information from the replay event API."""

    def __init__(self, detail_json: dict) -> None:
        """Initialize an event detail.

        Args:
            detail_json: Raw data from the replayEvent API.
        """
        self._detail_json = detail_json

    @property
    def event_id(self) -> str:
        """Return the event ID."""
        return self._detail_json.get("eventId", "")

    @property
    def channel_id(self) -> str:
        """Return the channel ID."""
        return self._detail_json.get("channelId", "")

    @property
    def title(self) -> str:
        """Return the program title."""
        return self._detail_json.get("title", "")

    @property
    def episode_name(self) -> Optional[str]:
        """Return the episode name."""
        return self._detail_json.get("episodeName")

    @property
    def short_description(self) -> Optional[str]:
        """Return the short description."""
        return self._detail_json.get("shortDescription")

    @property
    def long_description(self) -> Optional[str]:
        """Return the long description."""
        return self._detail_json.get("longDescription")

    @property
    def description(self) -> Optional[str]:
        """Return the best available description (long preferred over short)."""
        return self.long_description or self.short_description

    @property
    def genres(self) -> List[str]:
        """Return list of genre names."""
        return self._detail_json.get("genres", [])

    @property
    def season_number(self) -> Optional[int]:
        """Return the season number."""
        return self._detail_json.get("seasonNumber")

    @property
    def episode_number(self) -> Optional[int]:
        """Return the episode number."""
        return self._detail_json.get("episodeNumber")

    @property
    def start_time(self) -> Optional[float]:
        """Return the start time as Unix timestamp in seconds."""
        return self._detail_json.get("startTime")

    @property
    def end_time(self) -> Optional[float]:
        """Return the end time as Unix timestamp in seconds."""
        return self._detail_json.get("endTime")

    @property
    def actors(self) -> List[str]:
        """Return list of actor names."""
        return self._detail_json.get("actors", [])

    @property
    def directors(self) -> List[str]:
        """Return list of director names."""
        return self._detail_json.get("directors", [])

    @property
    def producers(self) -> List[str]:
        """Return list of producer names."""
        return self._detail_json.get("producers", [])

    @property
    def country_of_origin(self) -> Optional[str]:
        """Return the country of origin code."""
        return self._detail_json.get("countryOfOrigin")

    @property
    def production_date(self) -> Optional[str]:
        """Return the production date."""
        return self._detail_json.get("productionDate")

    @property
    def minimum_age(self) -> Optional[str]:
        """Return the minimum age rating."""
        return self._detail_json.get("minimumAge")

    @property
    def image_version(self) -> Optional[str]:
        """Return the image version identifier."""
        return self._detail_json.get("imageVersion")

    @property
    def series_id(self) -> Optional[str]:
        """Return the series ID."""
        return self._detail_json.get("seriesId")

    @property
    def parent_series_id(self) -> Optional[str]:
        """Return the parent series ID."""
        return self._detail_json.get("parentSeriesId")

    @property
    def audio_languages(self) -> List[str]:
        """Return list of audio language codes."""
        langs = self._detail_json.get("audioLanguages", [])
        return [item.get("lang", "") for item in langs if isinstance(item, dict)]

    @property
    def caption_languages(self) -> List[str]:
        """Return list of caption/subtitle language codes."""
        langs = self._detail_json.get("captionLanguages", [])
        return [item.get("lang", "") for item in langs if isinstance(item, dict)]


class LGHorizonReplayChannel:
    """A channel that supports replay/catch-up TV."""

    def __init__(self, channel_json: dict) -> None:
        """Initialize a replay channel.

        Args:
            channel_json: Raw channel data from the replay catalog API.
        """
        self._channel_json = channel_json

    @property
    def id(self) -> str:
        """Return the channel ID."""
        return self._channel_json.get("id", "")

    @property
    def name(self) -> str:
        """Return the channel name."""
        return self._channel_json.get("name", "")

    @property
    def logo(self) -> str:
        """Return the channel logo URL."""
        return self._channel_json.get("logo", "")


class LGHorizonManagedRecording:
    """A recording from the recording management service with extended details."""

    def __init__(self, recording_json: dict) -> None:
        """Initialize a managed recording.

        Args:
            recording_json: Raw recording data from the recording management API.
        """
        self._recording_json = recording_json

    @property
    def id(self) -> str:
        """Return the recording ID."""
        return self._recording_json.get("id", "")

    @property
    def title(self) -> str:
        """Return the recording title."""
        return self._recording_json.get("title", "")

    @property
    def show_name(self) -> Optional[str]:
        """Return the show name."""
        return self._recording_json.get("showName")

    @property
    def season_name(self) -> Optional[str]:
        """Return the season name."""
        return self._recording_json.get("seasonName")

    @property
    def item_type(self) -> str:
        """Return the item type (e.g. 'single')."""
        return self._recording_json.get("itemType", "")

    @property
    def recording_state(self) -> str:
        """Return the recording state (recorded, planned, partiallyRecorded)."""
        return self._recording_json.get("recordingState", "")

    @property
    def recording_type(self) -> str:
        """Return the recording type (e.g. 'nDVR')."""
        return self._recording_json.get("recordingType", "")

    @property
    def channel_id(self) -> Optional[str]:
        """Return the channel ID."""
        return self._recording_json.get("channelId")

    @property
    def season_number(self) -> Optional[int]:
        """Return the season number."""
        return self._recording_json.get("seasonNumber")

    @property
    def episode_number(self) -> Optional[int]:
        """Return the episode number."""
        return self._recording_json.get("episodeNumber")

    @property
    def season_id(self) -> Optional[str]:
        """Return the season ID."""
        return self._recording_json.get("seasonId")

    @property
    def show_id(self) -> Optional[str]:
        """Return the show ID."""
        return self._recording_json.get("showId")

    @property
    def source(self) -> Optional[str]:
        """Return the recording source (e.g. 'show')."""
        return self._recording_json.get("source")

    @property
    def disk_space(self) -> float:
        """Return the disk space used in hours."""
        return self._recording_json.get("diskSpace", 0.0)

    @property
    def duration(self) -> Optional[int]:
        """Return the recording duration in seconds."""
        return self._recording_json.get("recDuration")

    @property
    def start_time(self) -> Optional[str]:
        """Return the display start time (ISO 8601)."""
        return self._recording_json.get("displayStartTime") or self._recording_json.get("startTime")

    @property
    def end_time(self) -> Optional[str]:
        """Return the display end time (ISO 8601)."""
        return self._recording_json.get("displayEndTime") or self._recording_json.get("endTime")

    @property
    def rec_start_time(self) -> Optional[str]:
        """Return the actual recording start time including padding (ISO 8601)."""
        return self._recording_json.get("recStartTime")

    @property
    def rec_end_time(self) -> Optional[str]:
        """Return the actual recording end time including padding (ISO 8601)."""
        return self._recording_json.get("recEndTime")

    @property
    def delete_time(self) -> Optional[str]:
        """Return when this recording will be auto-deleted (ISO 8601)."""
        return self._recording_json.get("deleteTime")

    @property
    def booking_time(self) -> Optional[str]:
        """Return when this recording was scheduled (ISO 8601)."""
        return self._recording_json.get("bookingTime")

    @property
    def retention_period(self) -> Optional[int]:
        """Return the retention period in days."""
        return self._recording_json.get("retentionPeriod")

    @property
    def pre_padding_offset(self) -> Optional[int]:
        """Return the pre-recording padding in seconds."""
        return self._recording_json.get("prePaddingOffset")

    @property
    def post_padding_offset(self) -> Optional[int]:
        """Return the post-recording padding in seconds."""
        return self._recording_json.get("postPaddingOffset")

    @property
    def is_premiere(self) -> bool:
        """Return whether this is a premiere."""
        return self._recording_json.get("isPremiere", False)

    @property
    def is_adult(self) -> bool:
        """Return whether this is adult content."""
        return self._recording_json.get("isAdult", False)

    @property
    def minimum_age(self) -> Optional[str]:
        """Return the minimum age rating."""
        return self._recording_json.get("minimumAge")

    @property
    def auto_deletion_protected(self) -> bool:
        """Return whether auto-deletion is prevented."""
        return self._recording_json.get("autoDeletionProtected", False)


class LGHorizonManagedRecordingList:
    """List of managed recordings with pagination info."""

    def __init__(self, response_json: dict) -> None:
        """Initialize the managed recording list.

        Args:
            response_json: Raw response from the recording management API.
        """
        self._total = response_json.get("total", 0)
        self._limit = response_json.get("limit", 0)
        self._offset = response_json.get("offset", 0)
        self._recordings = [
            LGHorizonManagedRecording(item)
            for item in response_json.get("data", [])
        ]

    @property
    def total(self) -> int:
        """Return the total number of recordings available."""
        return self._total

    @property
    def limit(self) -> int:
        """Return the page size limit used."""
        return self._limit

    @property
    def offset(self) -> int:
        """Return the offset used."""
        return self._offset

    @property
    def recordings(self) -> List[LGHorizonManagedRecording]:
        """Return the list of managed recordings."""
        return self._recordings

    @property
    def total_disk_space(self) -> float:
        """Return total disk space used in hours."""
        return sum(r.disk_space for r in self._recordings)
