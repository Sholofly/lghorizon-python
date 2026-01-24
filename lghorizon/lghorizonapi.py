"""LG Horizon API client."""

from typing import Any
from .models.lghorizon_auth import LGHorizonAuth
from .models.lghorizon_config import LGHorizonServicesConfig
from .models.lghorizon_customer import LGHorizonCustomer


class LGHorizonApi:
    """LG Horizon API client."""

    def __init__(self, auth: LGHorizonAuth) -> None:
        """Initialize LG Horizon API client."""
        self.auth = auth
        self._service_config: LGHorizonServicesConfig | None = None

    @property
    def service_config(self) -> LGHorizonServicesConfig:
        """Return the service config, or raise if not initialized."""
        if self._service_config is None:
            raise RuntimeError("Service configuration not initialized")
        return self._service_config

    async def initialize(self) -> None:
        """Initialize the API client."""
        await self._get_config()
        await self._get_mqtt_token()
        await self._get_customer_info()

    async def _get_config(self):
        base_country_code = self.auth.country_code[0:2]
        result = await self.auth.request(
            self.auth.host,
            f"/{base_country_code}/en/config-service/conf/web/backoffice.json",
        )
        self._service_config = LGHorizonServicesConfig(result)

    async def _get_mqtt_token(self) -> Any:
        """Get the MQTT token."""
        service_url = await self.service_config.get_service_url("authorizationService")
        result = await self.auth.request(
            service_url,
            "/v1/mqtt/token",
        )
        return result["token"]

    async def _get_customer_info(self) -> Any:
        service_url = await self.service_config.get_service_url(
            "personalizationService"
        )
        result = await self.auth.request(
            service_url,
            f"/v1/customer/{self.auth.household_id}?with=profiles%2Cdevices",
        )
        return LGHorizonCustomer(result)


__all__ = ["LGHorizonApi", "LGHorizonAuth"]
