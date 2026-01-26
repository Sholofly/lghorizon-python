"""LG Horizon API client."""

import logging
from typing import Any, Dict, cast

from .models.lghorizon_device import LGHorizonDevice
from .models.lghorizon_channel import LGHorizonChannel
from .models.lghorizon_auth import LGHorizonAuth
from .models.lghorizon_customer import LGHorizonCustomer
from .models.lghorizon_mqtt_client import LGHorizonMqttClient
from .models.lghorizon_config import LGHorizonServicesConfig
from .models.lghorizon_entitlements import LGHorizonEntitlements
from .models.lghorizon_profile import LGHorizonProfile
from .models.lghorizon_message import LGHorizonMessageType
from .message_factory import LGHorizonMessageFactory
from .models.lghorizon_message import LGHorizonStatusMessage, LGHorizonUIStatusMessage

_LOGGER = logging.getLogger(__name__)


class LGHorizonApi:
    """LG Horizon API client."""

    _mqtt_client: LGHorizonMqttClient
    auth: LGHorizonAuth
    _service_config: LGHorizonServicesConfig
    _customer: LGHorizonCustomer
    _channels: Dict[str, LGHorizonChannel]
    _entitlements: LGHorizonEntitlements
    _profile_id: str
    _initialized: bool = False
    _devices: Dict[str, LGHorizonDevice] = {}
    _message_factory: LGHorizonMessageFactory = LGHorizonMessageFactory()

    def __init__(self, auth: LGHorizonAuth, profile_id: str = "") -> None:
        """Initialize LG Horizon API client."""
        self.auth = auth
        self._profile_id = profile_id
        self._channels = {}

    async def initialize(self) -> None:
        """Initialize the API client."""
        self._service_config = await self.auth.get_service_config()
        self._customer = await self._get_customer_info()
        await self._refresh_entitlements()
        await self._refresh_channels()
        self._mqtt_client = await self._create_mqtt_client()
        await self._mqtt_client.connect()
        await self._register_devices()
        self._initialized = True

    async def get_devices(self) -> Dict[str, LGHorizonDevice]:
        """Get devices."""
        if not self._initialized:
            raise RuntimeError("LGHorizonApi not initialized")

        return self._devices

    async def get_profiles(self) -> Dict[str, LGHorizonProfile]:
        """Get profile IDs."""
        if not self._initialized:
            raise RuntimeError("LGHorizonApi not initialized")

        return self._customer.profiles

    async def get_profile_channels(
        self, profile_id: str
    ) -> Dict[str, LGHorizonChannel]:
        """Returns channels to display baed on profile."""
        # Attempt to retrieve the profile by the given profile_id
        profile = self._customer.profiles.get(profile_id)

        # If the specified profile is not found, and there are other profiles available,
        # default to the first profile in the customer's list.
        if not profile and self._customer.profiles:
            _LOGGER.debug(
                "Profile with ID '%s' not found. Defaulting to first available profile.",
                profile_id,
            )
            profile = list(self._customer.profiles.values())[0]

        # If a profile is found and it has favorite channels, filter the main channels list.
        if profile and profile.favorite_channels:
            _LOGGER.debug("Returning favorite channels for profile '%s'.", profile.name)
            # Use a set for faster lookup of favorite channel IDs
            profile_channel_ids = set(profile.favorite_channels)
            return {
                channel.id: channel
                for channel in self._channels.values()
                if channel.id in profile_channel_ids
            }

        # If no profile is found (even after defaulting) or the profile has no favorite channels,
        # return all available channels.
        _LOGGER.debug("No specific profile channels found, returning all channels.")
        return self._channels

    async def _register_devices(self) -> None:
        """Register devices."""
        _LOGGER.debug("Registering devices...")
        self._devices = {}
        channels = await self.get_profile_channels(self._profile_id)
        for raw_box in self._customer.assigned_devices:
            _LOGGER.debug("Creating box for device: %s", raw_box)
            device = LGHorizonDevice(raw_box, self._mqtt_client, self.auth, channels)
            await device.register_mqtt()
            self._devices[device.device_id] = device

    async def disconnect(self) -> None:
        """Disconnect the client."""
        if self._mqtt_client:
            await self._mqtt_client.disconnect()
        self._initialized = False

    async def _create_mqtt_client(self) -> LGHorizonMqttClient:
        mqtt_client = await LGHorizonMqttClient.create(
            self.auth,
            self._on_mqtt_connected,
            self._on_mqtt_message,
        )
        return mqtt_client

    async def _on_mqtt_connected(self) -> None:
        """MQTT connected callback."""
        await self._mqtt_client.subscribe(self.auth.household_id)
        await self._mqtt_client.subscribe(self.auth.household_id + "/#")
        await self._mqtt_client.subscribe(
            self.auth.household_id + "/" + self._mqtt_client.client_id
        )
        await self._mqtt_client.subscribe(self.auth.household_id + "/+/status")
        await self._mqtt_client.subscribe(
            self.auth.household_id + "/+/networkRecordings"
        )
        await self._mqtt_client.subscribe(
            self.auth.household_id + "/+/networkRecordings/capacity"
        )
        await self._mqtt_client.subscribe(self.auth.household_id + "/+/localRecordings")
        await self._mqtt_client.subscribe(
            self.auth.household_id + "/+/localRecordings/capacity"
        )
        await self._mqtt_client.subscribe(self.auth.household_id + "/watchlistService")
        await self._mqtt_client.subscribe(self.auth.household_id + "/purchaseService")
        await self._mqtt_client.subscribe(
            self.auth.household_id + "/personalizationService"
        )
        await self._mqtt_client.subscribe(self.auth.household_id + "/recordingStatus")
        await self._mqtt_client.subscribe(
            self.auth.household_id + "/recordingStatus/lastUserAction"
        )

    async def _on_mqtt_message(self, mqtt_message: dict, mqtt_topic: str) -> None:
        """MQTT message callback."""
        message = await self._message_factory.create_message(mqtt_topic, mqtt_message)
        match message.message_type:
            case LGHorizonMessageType.STATUS:
                message.__class__ = LGHorizonStatusMessage
                status_message = cast(LGHorizonStatusMessage, message)
                await self._devices[status_message.source].handle_status_message(
                    status_message
                )
            case LGHorizonMessageType.UI_STATUS:
                message.__class__ = LGHorizonUIStatusMessage
                status_message = cast(LGHorizonUIStatusMessage, message)
                await self._devices[status_message.source].handle_ui_status_message(
                    status_message
                )

    async def _get_customer_info(self) -> Any:
        service_url = await self._service_config.get_service_url(
            "personalizationService"
        )
        result = await self.auth.request(
            service_url,
            f"/v1/customer/{self.auth.household_id}?with=profiles%2Cdevices",
        )
        return LGHorizonCustomer(result)

    async def _refresh_entitlements(self) -> Any:
        """Retrieve entitlements."""
        _LOGGER.debug("Retrieving entitlements...")
        service_url = await self._service_config.get_service_url("purchaseService")
        result = await self.auth.request(
            service_url,
            f"/v2/customers/{self.auth.household_id}/entitlements?enableDaypass=true",
        )
        self._entitlements = LGHorizonEntitlements(result)

    async def _refresh_channels(self):
        """Retrieve channels."""
        _LOGGER.debug("Retrieving channels...")
        service_url = await self._service_config.get_service_url("linearService")

        channels_json = await self.auth.request(
            service_url,
            f"/v2/channels?cityId={self._customer.city_id}&language={self._customer.country_id}&productClass=Orion-DASH",
        )
        for channel_json in channels_json:
            channel = LGHorizonChannel(channel_json)
            common_entitlements = list(
                set(self._entitlements.entitlement_ids) & set(channel.linear_products)
            )

            if len(common_entitlements) == 0:
                continue

            self._channels[channel.id] = channel


__all__ = ["LGHorizonApi", "LGHorizonAuth"]
