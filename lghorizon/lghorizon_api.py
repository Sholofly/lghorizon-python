"""LG Horizon API client."""

import logging
from typing import Any, Dict, cast, Callable, Optional

from .lghorizon_device import LGHorizonDevice
from .lghorizon_models import LGHorizonChannel
from .lghorizon_models import LGHorizonAuth
from .lghorizon_models import LGHorizonCustomer
from .lghorizon_mqtt_client import LGHorizonMqttClient
from .lghorizon_models import LGHorizonServicesConfig
from .lghorizon_models import LGHorizonEntitlements
from .lghorizon_models import LGHorizonProfile
from .lghorizon_models import LGHorizonMessageType
from .lghorizon_message_factory import LGHorizonMessageFactory
from .lghorizon_models import LGHorizonStatusMessage, LGHorizonUIStatusMessage
from .lghorizon_models import LGHorizonRunningState
from .lghorizon_models import (
    LGHorizonRecordingList,
    LGHorizonRecordingQuota,
    LGHorizonShowRecordingList,
)
from .lghorizon_recording_factory import LGHorizonRecordingFactory
from .lghorizon_device_state_processor import LGHorizonDeviceStateProcessor


_LOGGER = logging.getLogger(__name__)


class LGHorizonApi:
    """LG Horizon API client."""

    _mqtt_client: LGHorizonMqttClient | None
    auth: LGHorizonAuth
    _service_config: LGHorizonServicesConfig
    _customer: LGHorizonCustomer
    _channels: Dict[str, LGHorizonChannel]
    _entitlements: LGHorizonEntitlements
    _profile_id: Optional[str]
    _device_state_processor: LGHorizonDeviceStateProcessor | None

    def __init__(self, auth: LGHorizonAuth, profile_id: Optional[str]) -> None:
        """Initialize LG Horizon API client.

        Args:
            auth: The authentication object for API requests.
            profile_id: The ID of the user profile to use (optional).
        """
        self.auth = auth
        self._profile_id = profile_id
        self._channels = {}
        self._devices: Dict[str, LGHorizonDevice] = {}
        self._message_factory = LGHorizonMessageFactory()
        self._recording_factory = LGHorizonRecordingFactory()
        self._device_state_processor = None
        self._mqtt_client = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the API client."""
        self._service_config = await self.auth.get_service_config()
        self._customer = await self._get_customer_info()
        if not self._profile_id:
            self._profile_id = list(self._customer.profiles.keys())[0]
        await self._refresh_entitlements()
        await self._refresh_channels()
        self._mqtt_client = await self._create_mqtt_client()
        await self._mqtt_client.connect()
        await self._register_devices()
        self._device_state_processor = LGHorizonDeviceStateProcessor(
            self.auth, self._channels, self._customer, self._profile_id
        )
        self._initialized = True

    async def set_token_refresh_callback(
        self, token_refresh_callback: Callable[[str], None]
    ) -> None:
        """Set the token refresh callback."""
        self.auth.token_refresh_callback = token_refresh_callback

    async def get_devices(self) -> dict[str, LGHorizonDevice]:
        """Get devices."""
        if not self._initialized:
            raise RuntimeError("LGHorizonApi not initialized")

        return self._devices

    async def get_profiles(self) -> dict[str, LGHorizonProfile]:
        """Get profile IDs."""
        if not self._initialized:
            raise RuntimeError("LGHorizonApi not initialized")

        return self._customer.profiles

    @property
    def has_cloud_recording(self) -> bool:
        """Get profile IDs."""
        if not self._initialized:
            raise RuntimeError("LGHorizonApi not initialized")

        return self._customer.has_cloud_recording

    async def get_profile_channels(
        self, profile_id: Optional[str] = None
    ) -> Dict[str, LGHorizonChannel]:
        """Returns channels to display baed on profile."""
        # Attempt to retrieve the profile by the given profile_id
        if not profile_id:
            profile_id = self._profile_id
        profile = self._customer.profiles.get(profile_id)

        # If the specified profile is not found, and there are other profiles available,
        # default to the first profile in the customer's list if available.
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
            if self._device_state_processor is None:
                self._device_state_processor = LGHorizonDeviceStateProcessor(
                    self.auth, self._channels, self._customer, self._profile_id
                )
            device = LGHorizonDevice(
                raw_box,
                self._mqtt_client,
                self._device_state_processor,
                self.auth,
                channels,
            )
            self._devices[device.device_id] = device

    async def disconnect(self) -> None:
        """Disconnect the client."""
        if self._mqtt_client:
            await self._mqtt_client.disconnect()
        self._initialized = False

    async def _create_mqtt_client(self) -> LGHorizonMqttClient:
        """Create and configure the MQTT client.

        Returns: An initialized LGHorizonMqttClient instance.
        """
        mqtt_client = await LGHorizonMqttClient.create(
            self.auth,
            self._on_mqtt_connected,
            self._on_mqtt_message,
        )
        return mqtt_client

    async def _on_mqtt_connected(self):
        """MQTT connected callback."""
        await self._mqtt_client.subscribe("#")
        await self._mqtt_client.subscribe(self.auth.household_id)
        # await self._mqtt_client.subscribe(self.auth.household_id + "/#")
        # await self._mqtt_client.subscribe(self.auth.household_id + "/+/#")
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

    async def _on_mqtt_message(self, mqtt_message: dict, mqtt_topic: str):
        """MQTT message callback."""
        message = await self._message_factory.create_message(mqtt_topic, mqtt_message)
        match message.message_type:
            case LGHorizonMessageType.STATUS:
                status_message = cast(LGHorizonStatusMessage, message)
                device = self._devices.get(status_message.source, None)
                if not device:
                    return
                await device.handle_status_message(status_message)
            case LGHorizonMessageType.UI_STATUS:
                ui_status_message = cast(LGHorizonUIStatusMessage, message)
                device = self._devices.get(ui_status_message.source, None)
                if not device:
                    return
                if (
                    not device.device_state.state
                    == LGHorizonRunningState.ONLINE_RUNNING
                ):
                    return
                await device.handle_ui_status_message(ui_status_message)

    async def _get_customer_info(self) -> LGHorizonCustomer:
        service_url = self._service_config.get_service_url(
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
        service_url = self._service_config.get_service_url("purchaseService")
        result = await self.auth.request(
            service_url,
            f"/v2/customers/{self.auth.household_id}/entitlements?enableDaypass=true",
        )
        self._entitlements = LGHorizonEntitlements(result)

    async def _refresh_channels(self):
        """Retrieve channels."""
        _LOGGER.debug("Retrieving channels...")
        service_url = self._service_config.get_service_url("linearService")
        lang = self._customer.get_profile_lang(self._profile_id)
        channels_json = await self.auth.request(
            service_url,
            f"/v2/channels?cityId={self._customer.city_id}&language={lang}&productClass=Orion-DASH",
        )
        for channel_json in channels_json:
            channel = LGHorizonChannel(channel_json)
            common_entitlements = list(
                set(self._entitlements.entitlement_ids) & set(channel.linear_products)
            )

            if len(common_entitlements) == 0:
                continue

            self._channels[channel.id] = channel

    async def get_all_recordings(self) -> LGHorizonRecordingList:
        """Retrieve all recordings."""
        if not self._customer.has_cloud_recording:
            return LGHorizonRecordingList([])
        _LOGGER.debug("Retrieving recordings...")
        service_url = self._service_config.get_service_url("recordingService")
        lang = self._customer.get_profile_lang(self._profile_id)
        recordings_json = await self.auth.request(
            service_url,
            f"/customers/{self.auth.household_id}/recordings?isAdult=false&offset=0&limit=100&sort=time&sortOrder=desc&profileId={self._profile_id}&language={lang}",
        )
        recordings = await self._recording_factory.create_recordings(recordings_json)
        return recordings

    async def get_show_recordings(
        self, show_id: str, channel_id: str
    ) -> LGHorizonShowRecordingList:  # type: ignore[valid-type]
        """Retrieve all recordings."""
        if not self._customer.has_cloud_recording:
            return LGHorizonShowRecordingList(None, None, [])
        _LOGGER.debug("Retrieving recordings fro show...")
        service_url = self._service_config.get_service_url("recordingService")
        lang = self._customer.get_profile_lang(self._profile_id)
        episodes_json = await self.auth.request(
            service_url,
            f"/customers/{self.auth.household_id}/episodes/shows/{show_id}?source=recording&isAdult=false&offset=0&limit=100&profileId={self._profile_id}&language={lang}&channelId={channel_id}&sort=time&sortOrder=asc",
        )
        recordings = await self._recording_factory.create_episodes(episodes_json)
        return recordings

    async def get_recording_quota(self) -> LGHorizonRecordingQuota:
        """Refresh recording quota."""
        _LOGGER.debug("Refreshing recording quota...")
        if not self._customer.has_cloud_recording:
            return LGHorizonRecordingQuota({})
        service_url = self._service_config.get_service_url("recordingService")
        quota_json = await self.auth.request(
            service_url,
            f"/customers/{self.auth.household_id}/quota",
        )
        return LGHorizonRecordingQuota(quota_json)


__all__ = ["LGHorizonApi", "LGHorizonAuth"]
