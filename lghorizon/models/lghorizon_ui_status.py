"""LG Horizon UI Status Model."""

from enum import Enum
from .lghorizon_sources import (
    LGHorizonSource,
    LGHorizonLinearSource,
    LGHorizonVODSource,
    LGHorizonReplaySource,
    LGHorizonNDVRSource,
    LGHorizonReviewBufferSource,
    LGHorizonUnknownSource,
    LGHorizonSourceType,
)


class LGHorizonUIStateType(Enum):
    """Enumeration of LG Horizon UI State types."""

    MAINUI = "mainUI"
    APPS = "apps"
    UNKNOWN = "unknown"


class LGHorizonPlayerState:
    """Represent the Player State of an LG Horizon device."""

    def __init__(self, raw_json: dict) -> None:
        """Initialize the Player State."""
        self._raw_json = raw_json

    @property
    def source_type(self) -> LGHorizonSourceType:
        """Return the source type."""
        return LGHorizonSourceType[self._raw_json.get("sourceType", "unknown").upper()]

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
            match self.source_type:
                case LGHorizonSourceType.LINEAR:
                    return LGHorizonLinearSource(self._raw_json["source"])
                case LGHorizonSourceType.VOD:
                    return LGHorizonVODSource(self._raw_json["source"])
                case LGHorizonSourceType.REPLAY:
                    return LGHorizonReplaySource(self._raw_json["source"])
                case LGHorizonSourceType.NDVR:
                    return LGHorizonNDVRSource(self._raw_json["source"])
                case LGHorizonSourceType.REVIEWBUFFER:
                    return LGHorizonReviewBufferSource(self._raw_json["source"])

        return LGHorizonUnknownSource(self._raw_json["source"])


class LGHorizonAppsState:
    """Represent the State of an LG Horizon device."""

    def __init__(self, raw_json: dict) -> None:
        """Initialize the Apps state."""
        self._raw_json = raw_json

    @property
    def id(self) -> str:
        """Return the id."""
        return self._raw_json.get("id", "")

    @property
    def app_name(self) -> str:
        """Return the app name."""
        return self._raw_json.get("appName", "")

    @property
    def logo_path(self) -> str:
        """Return the logo path."""
        return self._raw_json.get("logoPath", "")


class LGHorizonUIState:
    """Represent the State of an LG Horizon device."""

    _player_state: LGHorizonPlayerState | None = None
    _apps_state: LGHorizonAppsState | None = None

    def __init__(self, raw_json: dict) -> None:
        """Initialize the State."""
        self._raw_json = raw_json

    @property
    def ui_status(self) -> LGHorizonUIStateType:
        """Return the UI status dictionary."""
        return LGHorizonUIStateType[self._raw_json.get("uiStatus", "unknown").upper()]

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

    @property
    def apps_state(
        self,
    ) -> LGHorizonAppsState | None:  # Added None to the return type
        """Return the UI status dictionary."""
        # Check if _player_state is None and if "playerState" key exists in raw_json
        if self._apps_state is None and "appsState" in self._raw_json:
            self._apps_state = LGHorizonAppsState(
                self._raw_json["appsState"]
            )  # Access directly as existence is checked
        return self._apps_state
