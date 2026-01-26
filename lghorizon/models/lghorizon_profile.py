"""LG Horizon Profile model."""


class LGHorizonProfile:
    """LGHorizon profile."""

    def __init__(self, json_payload: dict):
        """Initialize a profile."""
        self._json_payload = json_payload

    @property
    def id(self) -> str:
        """Return the profile id."""
        return self._json_payload["profileId"]

    @property
    def name(self) -> str:
        """Return the profile name."""
        return self._json_payload["name"]

    @property
    def favorite_channels(self) -> list[str]:
        """Return the favorite channels."""
        return self._json_payload.get("favoriteChannels", [])
