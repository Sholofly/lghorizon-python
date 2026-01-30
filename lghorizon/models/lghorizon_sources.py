"LG Horizon Sources Model."

from abc import ABC, abstractmethod
from enum import Enum


class LGHorizonSourceType(Enum):
    """Enumeration of LG Horizon message types."""

    LINEAR = "linear"
    REVIEWBUFFER = "reviewBuffer"
    NDVR = "nDVR"
    REPLAY = "replay"
    VOD = "VOD"
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


class LGHorizonReviewBufferSource(LGHorizonSource):
    """Represent the ReviewBuffer Source of an LG Horizon device."""

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
        return LGHorizonSourceType.REVIEWBUFFER


class LGHorizonNDVRSource(LGHorizonSource):
    """Represent the ReviewBuffer Source of an LG Horizon device."""

    @property
    def recording_id(self) -> str:
        """Return the recording ID."""
        return self._raw_json.get("recordingId", "")

    @property
    def channel_id(self) -> str:
        """Return the channel ID."""
        return self._raw_json.get("channelId", "")

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.NDVR


class LGHorizonVODSource(LGHorizonSource):
    """Represent the VOD Source of an LG Horizon device."""

    @property
    def title_id(self) -> str:
        """Return the title ID."""
        return self._raw_json.get("titleId", "")

    @property
    def start_intro_time(self) -> int:
        """Return the start intro time."""
        return self._raw_json.get("startIntroTime", 0)

    @property
    def end_intro_time(self) -> int:
        """Return the end intro time."""
        return self._raw_json.get("endIntroTime", 0)

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.VOD


class LGHorizonReplaySource(LGHorizonSource):
    """Represent the VOD Source of an LG Horizon device."""

    @property
    def event_id(self) -> str:
        """Return the title ID."""
        return self._raw_json.get("eventId", "")

    @property
    def source_type(self) -> LGHorizonSourceType:
        """Return the source type."""
        return LGHorizonSourceType.REPLAY


class LGHorizonUnknownSource(LGHorizonSource):
    """Represent the Linear Source of an LG Horizon device."""

    @property
    def source_type(self) -> LGHorizonSourceType:
        return LGHorizonSourceType.UNKNOWN
