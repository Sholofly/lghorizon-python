"""LG Horizon message models."""

from typing import Optional
from enum import Enum


class LGHorizonReplayEvent:
    """LGhorizon replay event."""

    def __init__(self, raw_json: dict):
        """Initialize an LG Horizon replay event."""
        self._raw_json = raw_json

    @property
    def episode_number(self) -> Optional[int]:
        """Return the episode number."""
        return self._raw_json.get("episodeNumber")

    @property
    def channel_id(self) -> str:
        """Return the channel ID."""
        return self._raw_json["channelId"]

    @property
    def event_id(self) -> str:
        """Return the event ID."""
        return self._raw_json["eventId"]

    @property
    def season_number(self) -> Optional[int]:
        """Return the season number."""
        return self._raw_json.get("seasonNumber")

    @property
    def title(self) -> str:
        """Return the title of the event."""
        return self._raw_json["title"]

    @property
    def episode_name(self) -> Optional[str]:
        """Return the episode name."""
        return self._raw_json.get("episodeName", None)

    @property
    def full_episode_title(self) -> Optional[str]:
        """Return the full episode title."""

        if not self.season_number and not self.episode_number:
            return None
        full_title = f"""S{self.season_number:02d}E{self.episode_number:02d}"""
        if self.episode_name:
            full_title += f": {self.episode_name}"
        return full_title

    def __repr__(self) -> str:
        """Return a string representation of the replay event."""
        return f"LGHorizonReplayEvent(title='{self.title}', channel_id='{self.channel_id}', event_id='{self.event_id}')"


class LGHorizonVODType(Enum):
    """Enumeration of LG Horizon VOD types."""

    ASSET = "ASSET"
    EPISODE = "EPISODE"
    UNKNOWN = "UNKNOWN"


class LGHorizonVOD:
    """LGHorizon video on demand."""

    def __init__(self, vod_json) -> None:
        self._vod_json = vod_json

    @property
    def vod_type(self) -> LGHorizonVODType:
        """Return the ID of the VOD."""
        return LGHorizonVODType[self._vod_json.get("type", "unknown").upper()]

    @property
    def id(self) -> str:
        """Return the ID of the VOD."""
        return self._vod_json["id"]

    @property
    def episode_title(self) -> str:
        """Return the ID of the VOD."""
        match self.vod_type:
            case LGHorizonVODType.ASSET:
                return ""
            case LGHorizonVODType.EPISODE:
                return f"S{self._vod_json['season'].zfill(2)}E{self._vod_json['episode'].zfill(2)}: {self._vod_json['title']}"
        return ""

    @property
    def title(self) -> str:
        """Return the title of the VOD."""
        match self.vod_type:
            case LGHorizonVODType.ASSET:
                return self._vod_json["title"]
            case LGHorizonVODType.EPISODE:
                return self._vod_json["seriesTitle"]
        return "unknown"

    @property
    def duration(self) -> float:
        """Return the duration of the VOD."""
        return self._vod_json["duration"]
