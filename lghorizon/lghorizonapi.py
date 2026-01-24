"""LG Horizon API client."""

from typing import Any
from .models.lghorizon_auth import LGHorizonAuth
from .models.lghorizon_customer import LGHorizonCustomer
from .models.lghorizon_mqtt_client import LGHorizonMqttClient
from .models.lghorizon_config import LGHorizonServicesConfig


class LGHorizonApi:
    """LG Horizon API client."""

    _mqtt_client: LGHorizonMqttClient
    auth: LGHorizonAuth
    _service_config: LGHorizonServicesConfig
    _customer: LGHorizonCustomer

    def __init__(self, auth: LGHorizonAuth) -> None:
        """Initialize LG Horizon API client."""
        self.auth = auth

    async def initialize(self) -> None:
        """Initialize the API client."""
        self._service_config = await self.auth.get_service_config()
        self._customer = await self._get_customer_info()
        self._mqtt_client = await self._create_mqtt_client()
        self._mqtt_client.connect()

    async def _create_mqtt_client(self) -> LGHorizonMqttClient:
        mqtt_client = await LGHorizonMqttClient.create(
            self.auth,
            self._on_mqtt_connected,
            self._on_mqtt_message,
        )
        return mqtt_client

    async def _on_mqtt_connected(self) -> None:
        """MQTT connected callback."""
        pass

    async def _on_mqtt_message(self, message: str, topic: str) -> None:
        """MQTT message callback."""
        pass

    async def _get_customer_info(self) -> Any:
        service_url = await self._service_config.get_service_url(
            "personalizationService"
        )
        result = await self.auth.request(
            service_url,
            f"/v1/customer/{self.auth.household_id}?with=profiles%2Cdevices",
        )
        return LGHorizonCustomer(result)

    async def disconnect(self) -> None:
        """Disconnect the client."""
        await self._mqtt_client.disconnect()


__all__ = ["LGHorizonApi", "LGHorizonAuth"]
