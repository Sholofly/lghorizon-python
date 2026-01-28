"""LG Horizon message models."""

from abc import ABC, abstractmethod
import json

from enum import Enum
from .lghorizon_ui_status import LGHorizonUIState
from .lghorizon_device_state import LGHorizonRunningState


class LGHorizonMessageType(Enum):
    """Enumeration of LG Horizon message types."""

    UNKNOWN = 0
    STATUS = 1
    UI_STATUS = 2


class LGHorizonMessage(ABC):
    """Abstract base class for LG Horizon messages."""

    @property
    def topic(self) -> str:
        """Return the topic of the message."""
        return self._topic

    @property
    def payload(self) -> dict:
        """Return the payload of the message."""
        return self._payload

    @property
    @abstractmethod
    def message_type(self) -> LGHorizonMessageType | None:
        """Return the message type."""

    @abstractmethod
    def __init__(self, topic: str, payload: dict) -> None:
        """Abstract base class for LG Horizon messages."""
        self._topic = topic
        self._payload = payload

    def __repr__(self) -> str:
        """Return a string representation of the message."""
        return f"LGHorizonStatusMessage(topic='{self._topic}', payload={json.dumps(self._payload, indent=2)})"


class LGHorizonStatusMessage(LGHorizonMessage):
    """Represents an LG Horizon status message received via MQTT."""

    def __init__(self, payload: dict, topic: str) -> None:
        """Initialize an LG Horizon status message."""
        super().__init__(topic, payload)

    @property
    def message_type(self) -> LGHorizonMessageType:
        """Return the message type from the payload, if available."""
        return LGHorizonMessageType.STATUS

    @property
    def source(self) -> str:
        """Return the device ID from the payload, if available."""
        return self._payload.get("source", "unknown")

    @property
    def running_state(self) -> LGHorizonRunningState:
        """Return the device ID from the payload, if available."""
        return LGHorizonRunningState[self._payload.get("state", "unknown").upper()]


class LGHorizonUIStatusMessage(LGHorizonMessage):
    """Represents an LG Horizon UI status message received via MQTT."""

    _status: LGHorizonUIState | None = None

    def __init__(self, payload: dict, topic: str) -> None:
        """Initialize an LG Horizon UI status message."""
        super().__init__(topic, payload)

    @property
    def message_type(self) -> LGHorizonMessageType:
        """Return the message type from the payload, if available."""
        return LGHorizonMessageType.UI_STATUS

    @property
    def source(self) -> str:
        """Return the device ID from the payload, if available."""
        return self._payload.get("source", "unknown")

    @property
    def message_timestamp(self) -> int:
        """Return the device ID from the payload, if available."""
        return self._payload.get("messageTimeStamp", 0)

    @property
    def ui_state(self) -> LGHorizonUIState | None:
        """Return the device ID from the payload, if available."""
        if not self._status and "status" in self._payload:
            self._status = LGHorizonUIState(self._payload["status"])
        return self._status


class LGHorizonUnknownMessage(LGHorizonMessage):
    """Represents an unknown LG Horizon message received via MQTT."""

    def __init__(self, payload: dict, topic: str) -> None:
        """Initialize an LG Horizon unknown message."""
        super().__init__(topic, payload)

    @property
    def message_type(self) -> LGHorizonMessageType:
        """Return the message type from the payload, if available."""
        return LGHorizonMessageType.UNKNOWN
