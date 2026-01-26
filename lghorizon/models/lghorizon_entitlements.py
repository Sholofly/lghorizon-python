"""LG Horizon Entitlements model."""

from __future__ import annotations


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
