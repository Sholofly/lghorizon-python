"""LG Horizon Profile model."""


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
