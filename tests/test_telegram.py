"""Tests for Telegram webhook handler and message parsing."""

from unittest.mock import patch
from uuid import uuid4

import pytest

import app.telegram as telegram_module
from app.segmentation import SegmentationError
from app.telegram import (
    PARTICIPANT_MAP,
    _DEDUP_CAP,
    _processed_update_ids,
    extract_message,
    is_duplicate,
    process_telegram_update,
)

pytestmark = pytest.mark.anyio


def _make_update(text="hello world", username="jessie_tg", update_id=1001):
    """Build a minimal Telegram update payload."""
    return {
        "update_id": update_id,
        "message": {
            "message_id": 42,
            "from": {"id": 123, "is_bot": False, "username": username},
            "chat": {"id": 123, "type": "private"},
            "text": text,
        },
    }


@pytest.fixture(autouse=True)
def _clear_dedup_state():
    """Reset the in-memory dedup set and PARTICIPANT_MAP between tests."""
    _processed_update_ids.clear()
    telegram_module._dedup_cap_warned = False
    original_map = dict(PARTICIPANT_MAP)
    PARTICIPANT_MAP.clear()
    yield
    PARTICIPANT_MAP.clear()
    PARTICIPANT_MAP.update(original_map)
    telegram_module._dedup_cap_warned = False


# --- extract_message ---


def test_extract_message_valid_text():
    update = _make_update(text="morning walk", username="steveg", update_id=500)
    result = extract_message(update)
    assert result is not None
    text, participant, uid = result
    assert text == "morning walk"
    assert participant == "unknown"
    assert uid == 500


def test_extract_message_known_username():
    PARTICIPANT_MAP["jessie_tg"] = "jessie"
    update = _make_update(username="jessie_tg")
    result = extract_message(update)
    assert result is not None
    assert result[1] == "jessie"


def test_extract_message_unknown_username():
    update = _make_update(username="random_person")
    result = extract_message(update)
    assert result is not None
    assert result[1] == "unknown"


def test_extract_message_photo_returns_none():
    update = {
        "update_id": 100,
        "message": {
            "message_id": 1,
            "from": {"id": 1, "username": "test"},
            "chat": {"id": 1, "type": "private"},
            "photo": [{"file_id": "abc"}],
        },
    }
    assert extract_message(update) is None


def test_extract_message_empty_text_returns_none():
    update = _make_update(text="   ")
    assert extract_message(update) is None


def test_extract_message_no_message_field():
    update = {"update_id": 100}
    assert extract_message(update) is None


def test_extract_message_emma_by_username():
    PARTICIPANT_MAP.update({"emma_murf": "emma"})
    update = _make_update(username="emma_murf")
    result = extract_message(update)
    assert result is not None
    assert result[1] == "emma"


def test_extract_message_jessie_by_full_name():
    PARTICIPANT_MAP.update({"Jessie Lian": "jessie"})
    update = {
        "update_id": 200,
        "message": {
            "message_id": 42,
            "from": {"id": 100, "is_bot": False, "first_name": "Jessie", "last_name": "Lian"},
            "chat": {"id": 100, "type": "private"},
            "text": "hello",
        },
    }
    result = extract_message(update)
    assert result is not None
    assert result[1] == "jessie"


def test_extract_message_steven_by_full_name():
    PARTICIPANT_MAP.update({"Steven Gizzi": "steven"})
    update = {
        "update_id": 201,
        "message": {
            "message_id": 43,
            "from": {"id": 101, "is_bot": False, "first_name": "Steven", "last_name": "Gizzi"},
            "chat": {"id": 101, "type": "private"},
            "text": "hello",
        },
    }
    result = extract_message(update)
    assert result is not None
    assert result[1] == "steven"


def test_extract_message_first_name_fallback():
    PARTICIPANT_MAP.update({"Jessie": "jessie"})
    update = {
        "update_id": 202,
        "message": {
            "message_id": 44,
            "from": {"id": 100, "is_bot": False, "first_name": "Jessie"},
            "chat": {"id": 100, "type": "private"},
            "text": "hello",
        },
    }
    result = extract_message(update)
    assert result is not None
    assert result[1] == "jessie"


def test_extract_message_username_takes_precedence():
    PARTICIPANT_MAP.update({"emma_murf": "emma", "Emma Murphy": "emma"})
    update = {
        "update_id": 203,
        "message": {
            "message_id": 45,
            "from": {"id": 102, "is_bot": False, "username": "emma_murf", "first_name": "Emma", "last_name": "Murphy"},
            "chat": {"id": 102, "type": "private"},
            "text": "hello",
        },
    }
    result = extract_message(update)
    assert result is not None
    assert result[1] == "emma"


# --- is_duplicate ---


def test_is_duplicate_first_call_returns_false():
    assert is_duplicate(1) is False


def test_is_duplicate_second_call_returns_true():
    is_duplicate(2)
    assert is_duplicate(2) is True


# --- process_telegram_update ---


FAKE_EMBEDDING = [0.1] * 1536
FAKE_CLUSTER_ID = str(uuid4())
FAKE_EVENT_ID = str(uuid4())


def test_process_skips_non_text():
    result = process_telegram_update({"update_id": 1})
    assert result["processed"] is False
    assert result["reason"] == "not_text_message"


def test_process_skips_duplicate():
    update = _make_update(update_id=999)
    _processed_update_ids[999] = None
    result = process_telegram_update(update)
    assert result["processed"] is False
    assert result["reason"] == "duplicate"


@patch("app.telegram.update_event_xs")
@patch("app.telegram.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.telegram.increment_event_count")
@patch("app.telegram.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.telegram.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.telegram.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.telegram.generate_event_label", return_value="a meaningful moment")
def test_process_full_pipeline(mock_label, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    update = _make_update(text="a meaningful moment", update_id=777)
    result = process_telegram_update(update)
    assert result["processed"] is True
    assert result["event_id"] == FAKE_EVENT_ID
    mock_embed.assert_called_once_with("a meaningful moment")
    mock_insert.assert_called_once()
    mock_incr.assert_called_once_with(FAKE_CLUSTER_ID)


@patch("app.telegram.update_event_xs")
@patch("app.telegram.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.telegram.increment_event_count")
@patch("app.telegram.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.telegram.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.telegram.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.telegram.generate_event_label", return_value="a meaningful moment")
def test_process_pipeline_computes_xs(mock_label, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    update = _make_update(text="a meaningful moment", update_id=778)
    result = process_telegram_update(update)
    assert result["processed"] is True
    mock_xs.assert_called_once()
    xs_value = mock_xs.call_args[0][1]
    assert 0.0 <= xs_value <= 1.0


@patch("app.telegram.update_event_xs")
@patch("app.telegram.get_cluster_by_id", return_value={"name": "The Table", "event_count": 3})
@patch("app.telegram.increment_event_count")
@patch("app.telegram.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.telegram.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.telegram.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.telegram.generate_event_label", return_value="dinner together")
def test_process_pipeline_increments_event_count(mock_label, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    update = _make_update(text="dinner together", update_id=779)
    result = process_telegram_update(update)
    assert result["processed"] is True
    mock_incr.assert_called_once_with(FAKE_CLUSTER_ID)
    mock_cluster.assert_called_once_with(FAKE_CLUSTER_ID)


@patch("app.telegram.embed_text", side_effect=__import__("app.embedding", fromlist=["EmbeddingError"]).EmbeddingError("fail"))
def test_process_embedding_failure(mock_embed):
    update = _make_update(update_id=888)
    result = process_telegram_update(update)
    assert result["processed"] is False
    assert result["reason"] == "embedding_failed"


@patch("app.telegram.update_event_xs")
@patch("app.telegram.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.telegram.increment_event_count", side_effect=RuntimeError("RPC failed"))
@patch("app.telegram.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.telegram.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.telegram.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.telegram.generate_event_label", return_value="still works")
def test_telegram_increment_failure_event_survives(mock_label, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    update = _make_update(text="still works", update_id=890)
    result = process_telegram_update(update)
    assert result["processed"] is True
    assert result["event_id"] == FAKE_EVENT_ID
    mock_insert.assert_called_once()


# --- label generation ---


@patch("app.telegram.update_event_xs")
@patch("app.telegram.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.telegram.increment_event_count")
@patch("app.telegram.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.telegram.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.telegram.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.telegram.generate_event_label", return_value="Morning coffee ritual")
def test_telegram_uses_llm_label(mock_label, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    update = _make_update(text="Had my morning coffee on the porch", update_id=900)
    result = process_telegram_update(update)
    assert result["processed"] is True
    mock_insert.assert_called_once()
    assert mock_insert.call_args[1]["label"] == "Morning coffee ritual"


@patch("app.telegram.update_event_xs")
@patch("app.telegram.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.telegram.increment_event_count")
@patch("app.telegram.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.telegram.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.telegram.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.telegram.generate_event_label", side_effect=SegmentationError("API down"))
def test_telegram_label_failure_falls_back(mock_label, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    msg = "Had my morning coffee on the porch"
    update = _make_update(text=msg, update_id=901)
    result = process_telegram_update(update)
    assert result["processed"] is True
    mock_insert.assert_called_once()
    assert mock_insert.call_args[1]["label"] == msg[:80]


@patch("app.telegram.update_event_xs")
@patch("app.telegram.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.telegram.increment_event_count")
@patch("app.telegram.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.telegram.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.telegram.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.telegram.generate_event_label", return_value="Exact label passed through")
def test_telegram_label_content_passed_through(mock_label, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    update = _make_update(text="some message text", update_id=902)
    result = process_telegram_update(update)
    assert result["processed"] is True
    mock_label.assert_called_once_with("some message text")
    assert mock_insert.call_args[1]["label"] == "Exact label passed through"


# --- dedup cap (DEF-013) ---


def test_dedup_set_cap_enforced():
    for i in range(10_001):
        is_duplicate(i)
    assert len(_processed_update_ids) <= _DEDUP_CAP


def test_dedup_set_oldest_evicted():
    for i in range(1, 10_001):
        is_duplicate(i)
    assert len(_processed_update_ids) == _DEDUP_CAP
    # Adding 10_001 should evict ID 1
    is_duplicate(10_001)
    assert is_duplicate(1) is False  # evicted, so not a duplicate
    assert is_duplicate(10_000) is True  # still retained


# --- POST /telegram endpoint ---


async def test_post_telegram_valid_message(client):
    with patch("app.main.process_telegram_update", return_value={"processed": True, "reason": "ok", "event_id": "abc"}):
        response = await client.post("/telegram", json=_make_update())
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "skipped" not in data


async def test_post_telegram_empty_message(client):
    with patch("app.main.process_telegram_update", return_value={"processed": False, "reason": "not_text_message", "event_id": None}):
        response = await client.post("/telegram", json={"update_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["skipped"] is True


async def test_post_telegram_returns_200_on_internal_error(client):
    with patch("app.main.process_telegram_update", side_effect=RuntimeError("boom")):
        response = await client.post("/telegram", json=_make_update())
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
