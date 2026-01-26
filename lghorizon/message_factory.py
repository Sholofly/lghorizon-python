"LG Horizon Message Factory."

from .models.lghorizon_message import (
    LGHorizonMessage,
    LGHorizonStatusMessage,
    LGHorizonUnknownMessage,
    LGHorizonUIStatusMessage,
    LGHorizonMessageType,  # Import LGHorizonMessageType from here
)


class LGHorizonMessageFactory:
    """Handle incoming MQTT messages for LG Horizon devices."""

    def __init__(self):
        """Initialize the LG Horizon Message Factory."""

    async def create_message(self, topic: str, payload: dict) -> LGHorizonMessage:
        """Create an LG Horizon message based on the topic and payload."""
        message_type = await self._get_message_type(topic, payload)
        match message_type:
            case LGHorizonMessageType.STATUS:
                return LGHorizonStatusMessage(payload, topic)
            case LGHorizonMessageType.UI_STATUS:
                # Placeholder for UI_STATUS message handling
                return LGHorizonUIStatusMessage(payload, topic)
            case LGHorizonMessageType.UNKNOWN:
                return LGHorizonUnknownMessage(payload, topic)

    async def _get_message_type(
        self, topic: str, payload: dict
    ) -> LGHorizonMessageType:
        """Determine the message type based on topic and payload."""
        if "status" in topic:
            return LGHorizonMessageType.STATUS
        if "type" in payload:
            if payload["type"] == "CPE.uiStatus":
                return LGHorizonMessageType.UI_STATUS
        return LGHorizonMessageType.UNKNOWN
