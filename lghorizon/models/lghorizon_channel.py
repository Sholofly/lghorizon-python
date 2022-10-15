class LGHorizonChannel:
    """Represent a channel."""

    id: str
    title: str
    stream_image: str
    logo_image: str
    channel_number: str

    def __init__(self, channel_json):
        """Initialize a channel."""
        self.id = channel_json["id"]
        self.title = channel_json["name"]
        self.stream_image = self.get_stream_image(channel_json)
        self.logo_image = channel_json["logo"]["focused"]
        self.channel_number = channel_json["logicalChannelNumber"]
    
    def get_stream_image(self, channel_json)->str:
        image_stream = channel_json["imageStream"]
        if "full" in image_stream:
            return image_stream["full"]
        if "small" in image_stream:
            return image_stream["small"]
        logo = channel_json["logo"]
        if "focus" in logo:
            return logo["focus"]
        return ""

