"""LG Horizon device state model."""

from datetime import datetime
from typing import Optional
from enum import Enum
from .lghorizon_sources import LGHorizonSourceType


class LGHorizonRunningState(Enum):
    """Running state of horizon box."""

    UNKNOWN = "UNKNOWN"
    ONLINE_RUNNING = "ONLINE_RUNNING"
    ONLINE_STANDBY = "ONLINE_STANDBY"


class LGHorizonDeviceState:
    """Represent current state of a box."""

    _channel_id: Optional[str]
    _channel_name: Optional[str]
    _title: Optional[str]
    _image: Optional[str]
    _source_type: LGHorizonSourceType
    _paused: bool
    _sub_title: Optional[str]
    _duration: Optional[float]
    _position: Optional[float]
    _last_position_update: Optional[datetime]
    _state: LGHorizonRunningState
    _speed: Optional[int]

    def __init__(self) -> None:
        """Initialize the playing info."""
        self._channel_id = None
        self._title = None
        self._image = None
        self._source_type = LGHorizonSourceType.UNKNOWN
        self._paused = False
        self.sub_title = None
        self._duration = None
        self._position = None
        self._last_position_update = None
        self._state = LGHorizonRunningState.UNKNOWN
        self._speed = None
        self._channel_name = None

    @property
    def state(self) -> LGHorizonRunningState:
        """Return the channel ID."""
        return self._state

    @state.setter
    def state(self, value: LGHorizonRunningState) -> None:
        """Set the channel ID."""
        self._state = value

    @property
    def channel_id(self) -> Optional[str]:
        """Return the channel ID."""
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value: Optional[str]) -> None:
        """Set the channel ID."""
        self._channel_id = value

    @property
    def channel_name(self) -> Optional[str]:
        """Return the channel ID."""
        return self._channel_name

    @channel_name.setter
    def channel_name(self, value: Optional[str]) -> None:
        """Set the channel ID."""
        self._channel_name = value

    @property
    def title(self) -> Optional[str]:
        """Return the title."""
        return self._title

    @title.setter
    def title(self, value: Optional[str]) -> None:
        """Set the title."""
        self._title = value

    @property
    def image(self) -> Optional[str]:
        """Return the image URL."""
        return self._image

    @image.setter
    def image(self, value: Optional[str]) -> None:
        """Set the image URL."""
        self._image = value

    @property
    def source_type(self) -> LGHorizonSourceType:
        """Return the source type."""
        return self._source_type

    @source_type.setter
    def source_type(self, value: LGHorizonSourceType) -> None:
        """Set the source type."""
        self._source_type = value

    @property
    def paused(self) -> bool:
        """Return if the media is paused."""
        if self.speed is None:
            return False
        return self.speed == 0

    @property
    def sub_title(self) -> Optional[str]:
        """Return the channel title."""
        return self._sub_title

    @sub_title.setter
    def sub_title(self, value: Optional[str]) -> None:
        """Set the channel title."""
        self._sub_title = value

    @property
    def duration(self) -> Optional[float]:
        """Return the duration of the media."""
        return self._duration

    @duration.setter
    def duration(self, value: Optional[float]) -> None:
        """Set the duration of the media."""
        self._duration = value

    @property
    def position(self) -> Optional[float]:
        """Return the current position in the media."""
        return self._position

    @position.setter
    def position(self, value: Optional[float]) -> None:
        """Set the current position in the media."""
        self._position = value

    @property
    def last_position_update(self) -> Optional[datetime]:
        """Return the last time the position was updated."""
        return self._last_position_update

    @last_position_update.setter
    def last_position_update(self, value: Optional[datetime]) -> None:
        """Set the last position update time."""
        self._last_position_update = value

    async def reset_progress(self) -> None:
        """Reset the progress-related attributes."""
        self.last_position_update = None
        self.duration = None
        self.position = None

    @property
    def speed(self) -> Optional[int]:
        """Return the speed."""
        return self._speed

    @speed.setter
    def speed(self, value: int | None) -> None:
        """Set the channel ID."""
        self._speed = value

    async def reset(self) -> None:
        """Reset all playing information."""
        self.channel_id = None
        self.title = None
        self.sub_title = None
        self.image = None
        self.source_type = LGHorizonSourceType.UNKNOWN
        self.speed = None
        self.channel_name = None
        await self.reset_progress()
