from typing import Optional
from .lghorizon_models import (
    LGHorizonRecordingList,
    LGHorizonRecordingSingle,
    LGHorizonRecordingSeason,
    LGHorizonRecordingShow,
    LGHorizonRecordingType,
    LGHorizonShowRecordingList,
)


class LGHorizonRecordingFactory:
    """Factory to create LGHorizonRecording objects."""

    async def create_recordings(self, recording_json: dict) -> LGHorizonRecordingList:
        """Create a LGHorizonRecording object based on the recording type."""
        recording_list = []
        for recording in recording_json["data"]:
            recording_type = LGHorizonRecordingType[
                recording.get("type", "unknown").upper()
            ]
            match recording_type:
                case LGHorizonRecordingType.SINGLE:
                    recording_single = LGHorizonRecordingSingle(recording)
                    recording_list.append(recording_single)
                case LGHorizonRecordingType.SEASON:
                    recording_season = LGHorizonRecordingSeason(recording)
                    recording_list.append(recording_season)
                case LGHorizonRecordingType.SHOW:
                    recording_show = LGHorizonRecordingShow(recording)
                    recording_list.append(recording_show)
                case LGHorizonRecordingType.UNKNOWN:
                    pass

        return LGHorizonRecordingList(recording_list)

    async def create_episodes(self, episode_json: dict) -> LGHorizonShowRecordingList:
        """Create a LGHorizonRecording list based for episodes."""
        recording_list = []
        show_title: Optional[str] = None
        if "images" in episode_json:
            images = episode_json["images"]
            show_image = next(
                (img["url"] for img in images if img.get("type") == "titleTreatment"),
                images[0]["url"] if images else None,
            )
        else:
            show_image = None

        for recording in episode_json["data"]:
            recording_single = LGHorizonRecordingSingle(recording)
            if show_title is None:
                show_title = recording_single.show_title
            recording_list.append(recording_single)
        return LGHorizonShowRecordingList(show_title, show_image, recording_list)
