"""LGHorizon customer model."""

from typing import Dict
from .lghorizon_profile import LGHorizonProfile


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
