"""LG Horizon UI Status Model."""

from .lghorizon_sources import (
    LGHorizonSource,
    LGHorizonLinearSource,
    LGHorizonUnknownSource,
    LGHorizonSourceType,
)


class LGHorizonPlayerState:
    """Represent the Player State of an LG Horizon device."""

    def __init__(self, raw_json: dict) -> None:
        """Initialize the Player State."""
        self._raw_json = raw_json

    @property
    def source_type(self) -> str:
        """Return the source type."""
        return self._raw_json.get("sourceType", "")

    @property
    def speed(self) -> int:
        """Return the Player State dictionary."""
        return self._raw_json.get("speed", 0)

    @property
    def last_speed_change_time(
        self,
    ) -> int:
        """Return the last speed change time."""
        return self._raw_json.get("lastSpeedChangeTime", 0.0)

    @property
    def source(self) -> LGHorizonSource | None:  # Added None to the return type
        """Return the last speed change time."""
        if "source" in self._raw_json:
            source_type = LGHorizonSourceType[self.source_type.upper()]
            match source_type:
                case LGHorizonSourceType.LINEAR:
                    return LGHorizonLinearSource(self._raw_json["source"])

        return LGHorizonUnknownSource(self._raw_json["source"])


class LGHorizonUIState:
    """Represent the State of an LG Horizon device."""

    _player_state: LGHorizonPlayerState | None = None

    def __init__(self, raw_json: dict) -> None:
        """Initialize the State."""
        self._raw_json = raw_json

    @property
    def ui_status(self) -> str:
        """Return the UI status dictionary."""
        return self._raw_json.get("uiStatus", "")

    @property
    def player_state(
        self,
    ) -> LGHorizonPlayerState | None:  # Added None to the return type
        """Return the UI status dictionary."""
        # Check if _player_state is None and if "playerState" key exists in raw_json
        if self._player_state is None and "playerState" in self._raw_json:
            self._player_state = LGHorizonPlayerState(
                self._raw_json["playerState"]
            )  # Access directly as existence is checked
        return self._player_state
