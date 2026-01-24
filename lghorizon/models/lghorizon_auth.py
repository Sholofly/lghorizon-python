import time
import backoff

from typing import Any
from aiohttp import ClientSession, ClientResponseError
from requests import exceptions as request_exceptions
from ..const import COUNTRY_SETTINGS
from .exceptions import LGHorizonApiConnectionError, LGHorizonApiUnauthorizedError


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
        self.household_id = None
        self.token_expiry = None
        self.country_code = country_code
        self.host = COUNTRY_SETTINGS[country_code]["api_url"]
        self.use_refresh_token = COUNTRY_SETTINGS[country_code]["use_refreshtoken"]

    async def is_token_expiring(self) -> bool:
        """Check if the token is expiring within one day."""
        if not self.access_token or not self.token_expiry:
            return True
        current_unix_time = int(time.time())
        return current_unix_time >= (self.token_expiry - 86400)

    async def fetch_access_token(self) -> None:
        """Fetch the access token."""

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
            await self.fetch_access_token()
        try:
            clear_cookie = False
            if clear_cookie:
                self.websession.cookie_jar.clear()
            web_response = await self.websession.request(
                "GET",
                request_url,
                **kwargs,
                headers=headers,
            )
            web_response.raise_for_status()
            return await web_response.json()
        except ClientResponseError as cre:
            if cre.status == 401:
                await self.fetch_access_token()
            raise LGHorizonApiConnectionError(
                f"Unable to call {request_url}. Error:{str(cre)}"
            ) from cre
