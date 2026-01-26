"""LG Horizon Channel model."""


class LGHorizonChannel:
    """Class to represent a channel."""

    def __init__(self, channel_json):
        """Initialize a channel."""
        self.channel_json = channel_json

    @property
    def id(self) -> str:
        """Returns the id."""
        return self.channel_json["id"]

    @property
    def channel_number(self) -> str:
        """Returns the channel number."""
        return self.channel_json["logicalChannelNumber"]

    @property
    def is_radio(self) -> bool:
        """Returns if the channel is a radio channel."""
        return self.channel_json.get("isRadio", False)

    @property
    def title(self) -> str:
        """Returns the title."""
        return self.channel_json["name"]

    @property
    def logo_image(self) -> str:
        """Returns the logo image."""
        if "logo" in self.channel_json and "focused" in self.channel_json["logo"]:
            return self.channel_json["logo"]["focused"]
        return ""

    @property
    def linear_products(self) -> list[str]:
        """Returns the linear products."""
        return self.channel_json.get("linearProducts", [])

    @property
    def stream_image(self) -> str:
        """Returns the stream image."""
        image_stream = self.channel_json["imageStream"]
        if "full" in image_stream:
            return image_stream["full"]
        if "small" in image_stream:
            return image_stream["small"]
        if "logo" in self.channel_json and "focused" in self.channel_json["logo"]:
            return self.channel_json["logo"]["focused"]
        return ""
