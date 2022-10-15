class LGHorizonRecordingSingle:
    """Represents a single recording."""

    recording_id: str
    title: str
    image: str
    season: int = None
    episode: int = None

    def __init__(self, recording_json):
        """Init the single recording."""
        self.recording_id = recording_json["id"]
        self.title = recording_json["title"]
        self.image = recording_json["poster"]["url"]
        if "season" in recording_json:
            self.season = recording_json["season"]
        if "episode" in recording_json:
            self.episode = recording_json["episode"]