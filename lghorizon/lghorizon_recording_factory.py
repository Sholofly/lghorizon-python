from .lghorizon_models import (
    LGHorizonRecordingList,
    LGHorizonRecordingSingle,
    LGHorizonRecordingSeason,
    LGHorizonRecordingShow,
    LGHorizonRecordingType,
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

    async def create_episodes(self, episode_json: dict) -> LGHorizonRecordingList:
        """Create a LGHorizonRecording list based for episodes."""
        recording_list = []
        for recording in episode_json["data"]:
            recording_single = LGHorizonRecordingSingle(recording)
            recording_list.append(recording_single)
        return LGHorizonRecordingList(recording_list)
