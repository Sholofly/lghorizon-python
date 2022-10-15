class LGHorizonPlayingInfo:
    """Represent current state of a box."""

    channel_id: str = None
    title: str = None
    image: str = None
    source_type: str = None
    paused: bool = False
    channel_title: str = None

    def __init__(self):
        """Initialize the playing info."""
        pass

    def set_paused(self, paused: bool):
        """Set pause state."""
        self.paused = paused

    def set_channel(self, channel_id):
        """Set channel."""
        self.channel_id = channel_id

    def set_title(self, title):
        """Set title."""
        self.title = title

    def set_channel_title(self, title):
        """Set channel title."""
        self.channel_title = title

    def set_image(self, image):
        """Set image."""
        self.image = image

    def set_source_type(self, source_type):
        """Set sourfce type."""
        self.source_type = source_type

    def reset(self):
        self.channel_id = None
        self.title = None
        self.image = None
        self.source_type = None
        self.paused = False
        self.channel_title = None