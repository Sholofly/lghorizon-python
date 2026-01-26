"""LG Horizon Auth Model."""

import time
import logging
import json
from typing import Any

import backoff
from aiohttp import ClientResponseError, ClientSession

from ..const import COUNTRY_SETTINGS
from .exceptions import LGHorizonApiConnectionError, LGHorizonApiUnauthorizedError
from .lghorizon_config import LGHorizonServicesConfig

_LOGGER = logging.getLogger(__name__)


class LGHorizonAuth:
    """Class to make authenticated requests."""

    def __init__(
        self,
        websession: ClientSession,
        country_code: str,
        refresh_token: str = "",
        username: str = "",
        password: str = "",
    ) -> None:
        """Initialize the auth with refresh token."""
        self.websession = websession
        self.refresh_token = refresh_token
        self.access_token = None
        self.username = username
        self.password = password
        self.household_id = ""
        self.token_expiry = None
        self.country_code = country_code
        self.host = COUNTRY_SETTINGS[country_code]["api_url"]
        self.use_refresh_token = COUNTRY_SETTINGS[country_code]["use_refreshtoken"]
        self._service_config = None

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

        if not self.use_refresh_token and self.access_token is None:
            payload = {"password": self.password, "username": self.username}
            headers["x-device-code"] = "web"
            auth_url_path = "/auth-service/v1/authorization"
        else:
            payload = {"refreshToken": self.refresh_token}
            auth_url_path = "/auth-service/v1/authorization/refresh"
        try:
            auth_response = await self.websession.post(
                f"{self.host}{auth_url_path}",
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
    async def request(self, host: str, path: str, **kwargs) -> Any:
        """Make a request."""
        if headers := kwargs.pop("headers", {}):
            headers = dict(headers)
        request_url = f"{host}{path}"
        if await self.is_token_expiring():
            _LOGGER.debug("Access token is expiring, fetching a new one")
            await self.fetch_access_token()
        try:
            web_response = await self.websession.request(
                "GET",
                request_url,
                **kwargs,
                headers=headers,
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
        if self._service_config is None:
            base_country_code = self.country_code[0:2]
            result = await self.request(
                self.host,
                f"/{base_country_code}/en/config-service/conf/web/backoffice.json",
            )
            self._service_config = LGHorizonServicesConfig(result)

        return self._service_config
