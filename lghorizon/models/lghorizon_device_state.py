"""LG Horizon device state model."""

from datetime import datetime
from typing import Optional


class LGHorizonDeviceState:
    """Represent current state of a box."""

    _channel_id: Optional[str]
    _title: Optional[str]
    _image: Optional[str]
    _source_type: Optional[str]
    _paused: bool
    _channel_title: Optional[str]
    _duration: Optional[float]
    _position: Optional[float]
    _last_position_update: Optional[datetime]

    def __init__(self) -> None:
        """Initialize the playing info."""
        self._channel_id = None
        self._title = None
        self._image = None
        self._source_type = None
        self._paused = False
        self._channel_title = None
        self._duration = None
        self._position = None
        self._last_position_update = None

    @property
    def channel_id(self) -> Optional[str]:
        """Return the channel ID."""
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value: Optional[str]) -> None:
        """Set the channel ID."""
        self._channel_id = value

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
    def source_type(self) -> Optional[str]:
        """Return the source type."""
        return self._source_type

    @source_type.setter
    def source_type(self, value: Optional[str]) -> None:
        """Set the source type."""
        self._source_type = value

    @property
    def paused(self) -> bool:
        """Return if the media is paused."""
        return self._paused

    @paused.setter
    def paused(self, value: bool) -> None:
        """Set the paused state."""
        self._paused = value

    @property
    def channel_title(self) -> Optional[str]:
        """Return the channel title."""
        return self._channel_title

    @channel_title.setter
    def channel_title(self, value: Optional[str]) -> None:
        """Set the channel title."""
        self._channel_title = value

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

    def reset_progress(self) -> None:
        """Reset the progress-related attributes."""
        self.last_position_update = None
        self.duration = None
        self.position = None

    def reset(self) -> None:
        """Reset all playing information."""
        self.channel_id = None
        self.title = None
        self.image = None
        self.source_type = None
        self.paused = False
        self.channel_title = None
        self.reset_progress()
