"LG Horizon Sources Model."

from abc import ABC, abstractmethod
from enum import Enum


class LGHorizonSourceType(Enum):
    """Enumeration of LG Horizon message types."""

    LINEAR = "linear"
    UNKNOWN = "unknown"


class LGHorizonSource(ABC):
    """Abstract base class for LG Horizon sources."""

    def __init__(self, raw_json: dict) -> None:
        """Initialize the LG Horizon source."""
        self._raw_json = raw_json

    @property
    @abstractmethod
    def source_type(self) -> LGHorizonSourceType:
        """Return the message type."""


class LGHorizonLinearSource(LGHorizonSource):
    """Represent the Linear Source of an LG Horizon device."""

    @property
    def channel_id(self) -> str:
        """Return the source type."""
        return self._raw_json.get("channelId", "")

    @property
    def event_id(self) -> str:
        """Return the event ID."""
        return self._raw_json.get("eventId", "")

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.LINEAR


class LGHorizonUnknownSource(LGHorizonSource):
    """Represent the Linear Source of an LG Horizon device."""

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.UNKNOWN
