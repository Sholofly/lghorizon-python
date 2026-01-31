"""LG Horizon Model."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import backoff
from aiohttp import ClientResponseError, ClientSession

from .const import (
    COUNTRY_SETTINGS,
)
from .exceptions import LGHorizonApiConnectionError, LGHorizonApiUnauthorizedError


_LOGGER = logging.getLogger(__name__)


class LGHorizonRunningState(Enum):
    """Running state of horizon box."""

    UNKNOWN = "UNKNOWN"
    ONLINE_RUNNING = "ONLINE_RUNNING"
    ONLINE_STANDBY = "ONLINE_STANDBY"


class LGHorizonMessageType(Enum):
    """Enumeration of LG Horizon message types."""

    UNKNOWN = 0
    STATUS = 1
    UI_STATUS = 2


class LGHorizonRecordingSource(Enum):
    """LGHorizon recording."""

    SHOW = "show"
    UNKNOWN = "unknown"


class LGHorizonRecordingState(Enum):
    """Enumeration of LG Horizon recording states."""

    RECORDED = "recorded"
    UNKNOWN = "unknown"


class LGHorizonRecordingType(Enum):
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
        """Abstract base class for LG Horizon messages."""
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
        """Return the device ID from the payload, if available."""
        return LGHorizonRunningState[self._payload.get("state", "unknown").upper()]


class LGHorizonSourceType(Enum):
    """Enumeration of LG Horizon message types."""

    LINEAR = "linear"
    REVIEWBUFFER = "reviewBuffer"
    NDVR = "nDVR"
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
    def source_type(self) -> LGHorizonSourceType:
        """Return the message type."""


class LGHorizonLinearSource(LGHorizonSource):
    """Represent the Linear Source of an LG Horizon device."""

    @property
    def channel_id(self) -> str:
        """Return the source type."""
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
        """Return the source type."""
        return self._raw_json.get("channelId", "")

    @property
    def event_id(self) -> str:
        """Return the event ID."""
        return self._raw_json.get("eventId", "")

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.REVIEWBUFFER


class LGHorizonNDVRSource(LGHorizonSource):
    """Represent the ReviewBuffer Source of an LG Horizon device."""

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
    """Represent the VOD Source of an LG Horizon device."""

    @property
    def event_id(self) -> str:
        """Return the title ID."""
        return self._raw_json.get("eventId", "")

    @property
    def source_type(self) -> LGHorizonSourceType:
        """Return the source type."""
        return LGHorizonSourceType.REPLAY


class LGHorizonUnknownSource(LGHorizonSource):
    """Represent the Linear Source of an LG Horizon device."""

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
        return LGHorizonSourceType[self._raw_json.get("sourceType", "unknown").upper()]

    @property
    def speed(self) -> int:
        """Return the Player State dictionary."""
        return self._raw_json.get("speed", 0)

    @property
    def last_speed_change_time(
        self,
    ) -> int:
        """Return the last speed change time."""
        return self._raw_json.get("lastSpeedChangeTime", 0.0)

    @property
    def source(self) -> LGHorizonSource | None:  # Added None to the return type
        """Return the last speed change time."""
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

        return LGHorizonUnknownSource(self._raw_json["source"])


class LGHorizonAppsState:
    """Represent the State of an LG Horizon device."""

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
    """Represent the State of an LG Horizon device."""

    _player_state: LGHorizonPlayerState | None = None
    _apps_state: LGHorizonAppsState | None = None

    def __init__(self, raw_json: dict) -> None:
        """Initialize the State."""
        self._raw_json = raw_json

    @property
    def ui_status(self) -> LGHorizonUIStateType:
        """Return the UI status dictionary."""
        return LGHorizonUIStateType[self._raw_json.get("uiStatus", "unknown").upper()]

    @property
    def player_state(
        self,
    ) -> LGHorizonPlayerState | None:  # Added None to the return type
        """Return the UI status dictionary."""
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
        """Return the UI status dictionary."""
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
    def message_timestamp(self) -> int:
        """Return the device ID from the payload, if available."""
        return self._payload.get("messageTimeStamp", 0)

    @property
    def ui_state(self) -> LGHorizonUIState | None:
        """Return the device ID from the payload, if available."""
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

    def __init__(
        self,
        websession: ClientSession,
        country_code: str,
        refresh_token: str = "",
        username: str = "",
        password: str = "",
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

    async def is_token_expiring(self) -> bool:
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
            elif error:
                raise LGHorizonApiConnectionError(error["message"])
            else:
                raise LGHorizonApiConnectionError("Unknown connection error")

        self.household_id = auth_json["householdId"]
        self.access_token = auth_json["accessToken"]
        self.refresh_token = auth_json["refreshToken"]
        self.username = auth_json["username"]
        self.token_expiry = auth_json["refreshTokenExpiry"]

    @backoff.on_exception(backoff.expo, LGHorizonApiConnectionError, max_tries=3)
    async def request(self, host: str, path: str, params=None, **kwargs) -> Any:
        """Make a request."""
        if headers := kwargs.pop("headers", {}):
            headers = dict(headers)
        request_url = f"{host}{path}"
        if await self.is_token_expiring():  # Use property
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
                json.dumps(json_response, indent=2),
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
        service_url = await config.get_service_url("authorizationService")
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

    async def get_service_url(self, service_name: str) -> str:
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

    async def get_all_services(self) -> dict[str, str]:
        """Get all available services and their URLs.

        Returns:
            Dictionary mapping service names to URLs
        """
        return {
            name: url
            for name, service in self._config.items()
            if isinstance(service, dict) and (url := service.get("URL"))
        }

    async def __getattr__(self, name: str) -> Optional[str]:
        """Access service URLs as attributes.

        Example: config.authService returns the auth service URL

        Args:
            name: Service name

        Returns:
            URL for the service or None if not found
        """
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        return await self.get_service_url(name)

    def __repr__(self) -> str:
        """Return string representation."""
        services = list(self._config.keys())
        return f"LGHorizonConfig({len(services)} services)"


class LGHorizonCustomer:
    """LGHorizon customer."""

    _profiles: Dict[str, LGHorizonProfile] = {}

    def __init__(self, json_payload: dict):
        """Initialize a customer."""
        self._json_payload = json_payload

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

    async def get_profile_lang(self, profile_id: str) -> str:
        """Return the profile language."""
        if profile_id not in self.profiles:
            return "nl"
        return self.profiles[profile_id].options.lang


class LGHorizonDeviceState:
    """Represent current state of a box."""

    _channel_id: Optional[str]
    _channel_name: Optional[str]
    _title: Optional[str]
    _image: Optional[str]
    _source_type: LGHorizonSourceType
    _paused: bool
    _sub_title: Optional[str]
    _duration: Optional[float]
    _position: Optional[float]
    _last_position_update: Optional[datetime]
    _state: LGHorizonRunningState
    _speed: Optional[int]

    def __init__(self) -> None:
        """Initialize the playing info."""
        self._channel_id = None
        self._title = None
        self._image = None
        self._source_type = LGHorizonSourceType.UNKNOWN
        self._paused = False
        self.sub_title = None
        self._duration = None
        self._position = None
        self._last_position_update = None
        self._state = LGHorizonRunningState.UNKNOWN
        self._speed = None
        self._channel_name = None

    @property
    def state(self) -> LGHorizonRunningState:
        """Return the channel ID."""
        return self._state

    @state.setter
    def state(self, value: LGHorizonRunningState) -> None:
        """Set the channel ID."""
        self._state = value

    @property
    def channel_id(self) -> Optional[str]:
        """Return the channel ID."""
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value: Optional[str]) -> None:
        """Set the channel ID."""
        self._channel_id = value

    @property
    def channel_name(self) -> Optional[str]:
        """Return the channel ID."""
        return self._channel_name

    @channel_name.setter
    def channel_name(self, value: Optional[str]) -> None:
        """Set the channel ID."""
        self._channel_name = value

    @property
    def title(self) -> Optional[str]:
        """Return the title."""
        return self._title

    @title.setter
    def title(self, value: Optional[str]) -> None:
        """Set the title."""
        self._title = value

    @property
    def image(self) -> Optional[str]:
        """Return the image URL."""
        return self._image

    @image.setter
    def image(self, value: Optional[str]) -> None:
        """Set the image URL."""
        self._image = value

    @property
    def source_type(self) -> LGHorizonSourceType:
        """Return the source type."""
        return self._source_type

    @source_type.setter
    def source_type(self, value: LGHorizonSourceType) -> None:
        """Set the source type."""
        self._source_type = value

    @property
    def paused(self) -> bool:
        """Return if the media is paused."""
        if self.speed is None:
            return False
        return self.speed == 0

    @property
    def sub_title(self) -> Optional[str]:
        """Return the channel title."""
        return self._sub_title

    @sub_title.setter
    def sub_title(self, value: Optional[str]) -> None:
        """Set the channel title."""
        self._sub_title = value

    @property
    def duration(self) -> Optional[float]:
        """Return the duration of the media."""
        return self._duration

    @duration.setter
    def duration(self, value: Optional[float]) -> None:
        """Set the duration of the media."""
        self._duration = value

    @property
    def position(self) -> Optional[float]:
        """Return the current position in the media."""
        return self._position

    @position.setter
    def position(self, value: Optional[float]) -> None:
        """Set the current position in the media."""
        self._position = value

    @property
    def last_position_update(self) -> Optional[datetime]:
        """Return the last time the position was updated."""
        return self._last_position_update

    @last_position_update.setter
    def last_position_update(self, value: Optional[datetime]) -> None:
        """Set the last position update time."""
        self._last_position_update = value

    async def reset_progress(self) -> None:
        """Reset the progress-related attributes."""
        self.last_position_update = None
        self.duration = None
        self.position = None

    @property
    def speed(self) -> Optional[int]:
        """Return the speed."""
        return self._speed

    @speed.setter
    def speed(self, value: int | None) -> None:
        """Set the channel ID."""
        self._speed = value

    async def reset(self) -> None:
        """Reset all playing information."""
        self.channel_id = None
        self.title = None
        self.sub_title = None
        self.image = None
        self.source_type = LGHorizonSourceType.UNKNOWN
        self.speed = None
        self.channel_name = None
        await self.reset_progress()


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

    def __repr__(self) -> str:
        """Return a string representation of the replay event."""
        return f"LGHorizonReplayEvent(title='{self.title}', channel_id='{self.channel_id}', event_id='{self.event_id}')"


class LGHorizonVODType(Enum):
    """Enumeration of LG Horizon VOD types."""

    ASSET = "ASSET"
    EPISODE = "EPISODE"
    UNKNOWN = "UNKNOWN"


class LGHorizonVOD:
    """LGHorizon video on demand."""

    def __init__(self, vod_json) -> None:
        self._vod_json = vod_json

    @property
    def vod_type(self) -> LGHorizonVODType:
        """Return the ID of the VOD."""
        return LGHorizonVODType[self._vod_json.get("type", "unknown").upper()]

    @property
    def id(self) -> str:
        """Return the ID of the VOD."""
        return self._vod_json["id"]

    @property
    def season_number(self) -> Optional[int]:
        """Return the season number of the recording."""
        return self._vod_json.get("seasonNumber", None)

    @property
    def episode_number(self) -> Optional[int]:
        """Return the episode number of the recording."""
        return self._vod_json.get("episodeNumber", None)

    @property
    def full_episode_title(self) -> Optional[str]:
        """Return the ID of the VOD."""
        if self.vod_type != LGHorizonVODType.EPISODE:
            return None
        if not self.season_number and not self.episode_number:
            return None
        full_title = f"""S{self.season_number:02d}E{self.episode_number:02d}"""
        if self.title:
            full_title += f": {self.title}"
        return full_title

    @property
    def title(self) -> str:
        """Return the ID of the VOD."""
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
    """LGHorizon recording."""

    def __init__(self, episode_json: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        self._episode_json = episode_json

    @property
    def recording_state(self) -> LGHorizonRecordingState:
        """Return the recording state."""
        return LGHorizonRecordingState[
            self._episode_json.get("recordingState", "unknown").upper()
        ]

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
        """Return the payload of the message."""
        return self._recording_payload

    @property
    def recording_state(self) -> LGHorizonRecordingState:
        """Return the recording state."""
        return LGHorizonRecordingState[
            self._recording_payload.get("recordingState", "unknown").upper()
        ]

    @property
    def source(self) -> LGHorizonRecordingSource:
        """Return the recording source."""
        return LGHorizonRecordingSource[
            self._recording_payload.get("source", "unknown").upper()
        ]

    @property
    def type(self) -> LGHorizonRecordingType:
        """Return the recording source."""
        return LGHorizonRecordingType[
            self._recording_payload.get("type", "unknown").upper()
        ]

    @property
    def id(self) -> str:
        """Return the ID of the recording."""
        return self._recording_payload["id"]

    @property
    def title(self) -> str:
        """Return the title of the recording."""
        return self._recording_payload["title"]

    @property
    def channel_id(self) -> str:
        """Return the channel ID of the recording."""
        return self._recording_payload["channelId"]

    @property
    def poster_url(self) -> Optional[str]:
        """Return the title of the recording."""
        poster = self._recording_payload.get("poster")
        if poster:
            return poster.get("url")
        return None

    def __init__(self, recording_payload: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        self._recording_payload = recording_payload


class LGHorizonRecordingSingle(LGHorizonRecording):
    """LGHorizon recording."""

    @property
    def episode_title(self) -> Optional[str]:
        """Return the episode title of the recording."""
        return self._recording_payload.get("episodeTitle", None)

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
    def season_id(self) -> Optional[str]:
        """Return the season ID of the recording."""
        return self._recording_payload.get("seasonId", None)

    @property
    def full_episode_title(self) -> Optional[str]:
        """Return the full episode title of the recording."""
        if not self.season_number and not self.episode_number:
            return None
        full_title = f"""S{self.season_number:02d}E{self.episode_number:02d}"""
        if self.episode_title:
            full_title += f": {self.episode_title}"
        return full_title

    @property
    def channel_id(self) -> Optional[str]:
        """Return the channel ID of the recording."""
        return self._recording_payload.get("channelId", None)


class LGHorizonRecordingSeason(LGHorizonRecording):
    """LGHorizon recording."""

    _most_relevant_epsode: Optional[LGHOrizonRelevantEpisode]

    def __init__(self, payload: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        super().__init__(payload)
        episode_payload = payload.get("mostRelevantEpisode")
        if episode_payload:
            self._most_relevant_epsode = LGHOrizonRelevantEpisode(episode_payload)

    @property
    def no_of_episodes(self) -> int:
        """Return the number of episodes in the season."""
        return self._recording_payload.get("noOfEpisodes", 0)

    @property
    def season_title(self) -> str:
        """Return the season title of the recording."""
        return self._recording_payload.get("seasonTitle", "")

    @property
    def most_relevant_episode(self) -> Optional[LGHOrizonRelevantEpisode]:
        """Return the most relevant episode of the season."""
        return self._most_relevant_epsode


class LGHorizonRecordingShow(LGHorizonRecording):
    """LGHorizon recording."""

    _most_relevant_epsode: Optional[LGHOrizonRelevantEpisode]

    def __init__(self, payload: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        super().__init__(payload)
        episode_payload = payload.get("mostRelevantEpisode")
        if episode_payload:
            self._most_relevant_epsode = LGHOrizonRelevantEpisode(episode_payload)

    @property
    def no_of_episodes(self) -> int:
        """Return the number of episodes in the season."""
        return self._recording_payload.get("noOfEpisodes", 0)

    @property
    def most_relevant_episode(self) -> Optional[LGHOrizonRelevantEpisode]:
        """Return the most relevant episode of the season."""
        return self._most_relevant_epsode


class LGHorizonRecordingList:
    """LGHorizon recording."""

    @property
    def total(self) -> int:
        """Return the total number of recordings."""
        return len(self._recordings)

    def __init__(self, recordings: List[LGHorizonRecording]) -> None:
        """Abstract base class for LG Horizon recordings."""
        self._recordings = recordings


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
