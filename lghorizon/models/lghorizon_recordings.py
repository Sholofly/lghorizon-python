"""LG Horizon recoring models."""

from enum import Enum
from typing import Optional, List
from abc import ABC


class LGHorizonRecordingSource(Enum):
    """LGHorizon recording."""

    SHOW = "show"
    UNKNOWN = "unknown"


class LGHorizonRecordingState(Enum):
    """Enumeration of LG Horizon recording states."""

    RECORDED = "recorded"
    UNKNOWN = "unknown"


class LGHorizonRecordingType(Enum):
    """Enumeration of LG Horizon recording states."""

    SINGLE = "single"
    SEASON = "season"
    SHOW = "show"
    UNKNOWN = "unknown"


class LGHOrizonRelevantEpisode:
    """LGHorizon recording."""

    def __init__(self, episode_json: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        self._episode_json = episode_json

    @property
    def recording_state(self) -> LGHorizonRecordingState:
        """Return the recording state."""
        return LGHorizonRecordingState[
            self._episode_json.get("recordingState", "unknown").upper()
        ]

    @property
    def season_number(self) -> Optional[int]:
        """Return the season number of the recording."""
        return self._episode_json.get("seasonNumber", None)

    @property
    def episode_number(self) -> Optional[int]:
        """Return the episode number of the recording."""
        return self._episode_json.get("episodeNumber", None)


class LGHorizonRecording(ABC):
    """Abstract base class for LG Horizon recordings."""

    @property
    def recording_payload(self) -> dict:
        """Return the payload of the message."""
        return self._recording_payload

    @property
    def recording_state(self) -> LGHorizonRecordingState:
        """Return the recording state."""
        return LGHorizonRecordingState[
            self._recording_payload.get("recordingState", "unknown").upper()
        ]

    @property
    def source(self) -> LGHorizonRecordingSource:
        """Return the recording source."""
        return LGHorizonRecordingSource[
            self._recording_payload.get("source", "unknown").upper()
        ]

    @property
    def type(self) -> LGHorizonRecordingType:
        """Return the recording source."""
        return LGHorizonRecordingType[
            self._recording_payload.get("type", "unknown").upper()
        ]

    @property
    def id(self) -> str:
        """Return the ID of the recording."""
        return self._recording_payload["id"]

    @property
    def title(self) -> str:
        """Return the title of the recording."""
        return self._recording_payload["title"]

    @property
    def channel_id(self) -> str:
        """Return the channel ID of the recording."""
        return self._recording_payload["channelId"]

    @property
    def poster_url(self) -> Optional[str]:
        """Return the title of the recording."""
        poster = self._recording_payload.get("poster")
        if poster:
            return poster.get("url")
        return None

    def __init__(self, recording_payload: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        self._recording_payload = recording_payload


class LGHorizonRecordingSingle(LGHorizonRecording):
    """LGHorizon recording."""

    @property
    def episode_title(self) -> Optional[str]:
        """Return the episode title of the recording."""
        return self._recording_payload.get("episodeTitle", None)

    @property
    def season_number(self) -> Optional[int]:
        """Return the season number of the recording."""
        return self._recording_payload.get("seasonNumber", None)

    @property
    def episode_number(self) -> Optional[int]:
        """Return the episode number of the recording."""
        return self._recording_payload.get("episodeNumber", None)

    @property
    def show_id(self) -> Optional[str]:
        """Return the show ID of the recording."""
        return self._recording_payload.get("showId", None)

    @property
    def season_id(self) -> Optional[str]:
        """Return the season ID of the recording."""
        return self._recording_payload.get("seasonId", None)

    @property
    def full_episode_title(self) -> Optional[str]:
        """Return the full episode title of the recording."""
        if not self.season_number and not self.episode_number:
            return None
        full_title = f"""S{self.season_number:02d}E{self.episode_number:02d}"""
        if self.episode_title:
            full_title += f": {self.episode_title}"
        return full_title

    @property
    def channel_id(self) -> Optional[str]:
        """Return the channel ID of the recording."""
        return self._recording_payload.get("channelId", None)


class LGHorizonRecordingSeason(LGHorizonRecording):
    """LGHorizon recording."""

    _most_relevant_epsode: Optional[LGHOrizonRelevantEpisode]

    def __init__(self, payload: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        super().__init__(payload)
        episode_payload = payload.get("mostRelevantEpisode")
        if episode_payload:
            self._most_relevant_epsode = LGHOrizonRelevantEpisode(episode_payload)

    @property
    def no_of_episodes(self) -> int:
        """Return the number of episodes in the season."""
        return self._recording_payload.get("noOfEpisodes", 0)

    @property
    def season_title(self) -> str:
        """Return the season title of the recording."""
        return self._recording_payload.get("seasonTitle", "")

    @property
    def most_relevant_episode(self) -> Optional[LGHOrizonRelevantEpisode]:
        """Return the most relevant episode of the season."""
        return self._most_relevant_epsode


class LGHorizonRecordingShow(LGHorizonRecording):
    """LGHorizon recording."""

    _most_relevant_epsode: Optional[LGHOrizonRelevantEpisode]

    def __init__(self, payload: dict) -> None:
        """Abstract base class for LG Horizon recordings."""
        super().__init__(payload)
        episode_payload = payload.get("mostRelevantEpisode")
        if episode_payload:
            self._most_relevant_epsode = LGHOrizonRelevantEpisode(episode_payload)

    @property
    def no_of_episodes(self) -> int:
        """Return the number of episodes in the season."""
        return self._recording_payload.get("noOfEpisodes", 0)

    @property
    def most_relevant_episode(self) -> Optional[LGHOrizonRelevantEpisode]:
        """Return the most relevant episode of the season."""
        return self._most_relevant_epsode


class LGHorizonRecordingList:
    """LGHorizon recording."""

    @property
    def total(self) -> int:
        """Return the total number of recordings."""
        return len(self._recordings)

    def __init__(self, recordings: List[LGHorizonRecording]) -> None:
        """Abstract base class for LG Horizon recordings."""
        self._recordings = recordings


class LGHorizonRecordingQuota:
    """LGHorizon recording quota."""

    def __init__(self, quota_json: dict) -> None:
        """Initialize the recording quota."""
        self._quota_json = quota_json

    @property
    def quota(self) -> int:
        """Return the total space in MB."""
        return self._quota_json.get("quota", 0)

    @property
    def occupied(self) -> int:
        """Return the used space in MB."""
        return self._quota_json.get("occupied", 0)

    @property
    def percentage_used(self) -> float:
        """Return the percentage of space used."""
        if self.quota == 0:
            return 0.0
        return (self.occupied / self.quota) * 100
