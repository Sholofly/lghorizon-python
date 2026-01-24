class LGHorizonProfile:
    """LGHorizon profile."""

    profile_id: str | None = None
    name: str | None = None
    favorite_channels: list[str] | None = None

    def __init__(self, json_payload):
        self.profile_id = json_payload["profileId"]
        self.name = json_payload["name"]
        self.favorite_channels = json_payload["favoriteChannels"]
