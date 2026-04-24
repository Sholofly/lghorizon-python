"""Unit tests for helpers, LGHorizonMessageFactory, and LGHorizonRecordingFactory."""

import pytest

from lghorizon.helpers import make_id
from lghorizon.lghorizon_message_factory import LGHorizonMessageFactory
from lghorizon.lghorizon_recording_factory import LGHorizonRecordingFactory
from lghorizon.lghorizon_models import (
    LGHorizonStatusMessage,
    LGHorizonUIStatusMessage,
    LGHorizonUnknownMessage,
    LGHorizonRecordingList,
    LGHorizonRecordingSingle,
    LGHorizonRecordingSeason,
    LGHorizonRecordingShow,
    LGHorizonShowRecordingList,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# helpers.make_id
# ---------------------------------------------------------------------------


async def test_make_id_default_length():
    result = make_id()
    assert len(result) == 10


async def test_make_id_custom_length_8():
    result = make_id(8)
    assert len(result) == 8


async def test_make_id_custom_length_20():
    result = make_id(20)
    assert len(result) == 20


async def test_make_id_alphanumeric_only():
    result = make_id(50)
    assert result.isalnum()


async def test_make_id_unique():
    id1 = make_id()
    id2 = make_id()
    # With 62^10 possible values the probability of a collision is negligible
    assert id1 != id2


# ---------------------------------------------------------------------------
# LGHorizonMessageFactory
# ---------------------------------------------------------------------------


@pytest.fixture
def message_factory():
    return LGHorizonMessageFactory()


async def test_create_message_status_topic(
    message_factory, sample_status_payload
):
    topic = "household/device/status"
    message = await message_factory.create_message(topic, sample_status_payload)
    assert isinstance(message, LGHorizonStatusMessage)


async def test_create_message_ui_status_type(
    message_factory, sample_ui_status_payload
):
    topic = "household/device/uiUpdate"
    message = await message_factory.create_message(topic, sample_ui_status_payload)
    assert isinstance(message, LGHorizonUIStatusMessage)


async def test_create_message_unknown(message_factory):
    topic = "household/device/something"
    payload = {"foo": "bar"}
    message = await message_factory.create_message(topic, payload)
    assert isinstance(message, LGHorizonUnknownMessage)


async def test_status_topic_detection(message_factory, sample_status_payload):
    """Any topic containing 'status' should return a status message."""
    for topic in [
        "household/device/status",
        "prefix/status/suffix",
        "status",
    ]:
        message = await message_factory.create_message(topic, sample_status_payload)
        assert isinstance(message, LGHorizonStatusMessage), f"Failed for topic: {topic}"


async def test_ui_status_detection_requires_no_status_in_topic(
    message_factory, sample_ui_status_payload
):
    """CPE.uiStatus payload with a topic that does NOT contain 'status' → UIStatusMessage."""
    topic = "household/device/uiUpdate"
    message = await message_factory.create_message(topic, sample_ui_status_payload)
    assert isinstance(message, LGHorizonUIStatusMessage)


# ---------------------------------------------------------------------------
# LGHorizonRecordingFactory
# ---------------------------------------------------------------------------


@pytest.fixture
def recording_factory():
    return LGHorizonRecordingFactory()


async def test_create_recordings_mixed_types(
    recording_factory,
    sample_recording_single_json,
    sample_recording_season_json,
    sample_recording_show_json,
):
    recording_json = {
        "data": [
            sample_recording_single_json,
            sample_recording_season_json,
            sample_recording_show_json,
        ]
    }
    result = await recording_factory.create_recordings(recording_json)
    assert isinstance(result, LGHorizonRecordingList)
    assert result.total == 3
    assert isinstance(result.recordings[0], LGHorizonRecordingSingle)
    assert isinstance(result.recordings[1], LGHorizonRecordingSeason)
    assert isinstance(result.recordings[2], LGHorizonRecordingShow)


async def test_create_recordings_skips_unknown_types(recording_factory):
    recording_json = {
        "data": [
            {"id": "rec-unknown", "type": "unknown", "title": "Nope"},
        ]
    }
    result = await recording_factory.create_recordings(recording_json)
    assert result.total == 0


async def test_create_recordings_empty_data(recording_factory):
    result = await recording_factory.create_recordings({"data": []})
    assert isinstance(result, LGHorizonRecordingList)
    assert result.total == 0


async def test_create_episodes_returns_show_recording_list(
    recording_factory, sample_recording_single_json
):
    episode_json = {
        "data": [sample_recording_single_json],
        "images": [{"type": "poster", "url": "https://example.com/poster.png"}],
    }
    result = await recording_factory.create_episodes(episode_json)
    assert isinstance(result, LGHorizonShowRecordingList)
    assert result.total == 1


async def test_create_episodes_show_title(
    recording_factory, sample_recording_single_json
):
    episode_json = {
        "data": [sample_recording_single_json],
        "images": [],
    }
    result = await recording_factory.create_episodes(episode_json)
    # show_title comes from recording_single.show_title or .title
    assert result.show_title is not None


async def test_create_episodes_no_images_show_image_is_none(
    recording_factory, sample_recording_single_json
):
    episode_json = {
        "data": [sample_recording_single_json],
    }
    result = await recording_factory.create_episodes(episode_json)
    assert result.show_image is None


async def test_create_episodes_titletreatment_preferred(
    recording_factory, sample_recording_single_json
):
    episode_json = {
        "data": [sample_recording_single_json],
        "images": [
            {"type": "poster", "url": "https://example.com/poster.png"},
            {"type": "titleTreatment", "url": "https://example.com/title.png"},
        ],
    }
    result = await recording_factory.create_episodes(episode_json)
    assert result.show_image == "https://example.com/title.png"


async def test_create_episodes_falls_back_to_first_image(
    recording_factory, sample_recording_single_json
):
    episode_json = {
        "data": [sample_recording_single_json],
        "images": [
            {"type": "poster", "url": "https://example.com/poster.png"},
            {"type": "backdrop", "url": "https://example.com/backdrop.png"},
        ],
    }
    result = await recording_factory.create_episodes(episode_json)
    assert result.show_image == "https://example.com/poster.png"
