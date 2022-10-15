from .lghorizon_recording_single import LGHorizonRecordingSingle
from typing import List
class LGHorizonRecordingShow:
    """Represent a recorderd show."""

    title: str
    showId: str
    channelId: str
    image: str
    children: List[LGHorizonRecordingSingle] = []
    episode_count: int

    def __init__(self, recording_json):
        """Init recorder show."""
        self.showId = recording_json["showId"]
        self.title = recording_json["title"]
        self.image = recording_json["poster"]["url"]
        self.episode_count = recording_json["noOfEpisodes"]
        

    def append_child(self, season_recording: LGHorizonRecordingSingle):
        """Append child."""
        self.children.append(season_recording)