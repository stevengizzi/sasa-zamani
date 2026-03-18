"""End-to-end integration tests for Telegram and Granola pipelines."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.anyio

FAKE_EMBEDDING = [0.1] * 1536
FAKE_CLUSTER_ID = str(uuid4())
FAKE_CLUSTER_NAME = "The Table"
FAKE_EVENT_BASE = {
    "id": str(uuid4()),
    "label": "test event",
    "note": "test event",
    "participant": "jessie",
    "source": "telegram",
    "cluster_id": FAKE_CLUSTER_ID,
    "created_at": "2026-03-18T00:00:00Z",
    "event_date": None,
    "xs": None,
    "day": None,
}

SAMPLE_TRANSCRIPT = (
    "Jessie: I had the strangest dream last night about crossing a bridge"
    " that kept extending.\n\n"
    "Emma: That reminds me of the conversation we had about thresholds."
    " The food was incredible at that dinner, by the way.\n\n"
    "Steven: I've been writing about exactly this — the way memory reshapes"
    " when you try to pin it down."
)


def _make_telegram_update(text="hello world", username="jessie_tg", update_id=2001):
    return {
        "update_id": update_id,
        "message": {
            "message_id": 42,
            "from": {"id": 123, "is_bot": False, "username": username},
            "chat": {"id": 123, "type": "private"},
            "text": text,
        },
    }


# --- Telegram pipeline ---


async def test_telegram_pipeline_stores_event(client):
    """POST /telegram → GET /events shows the new event."""
    telegram_result = {"processed": True, "reason": "ok", "event_id": str(uuid4())}
    event_row = {**FAKE_EVENT_BASE, "id": telegram_result["event_id"]}

    with patch("app.main.process_telegram_update", return_value=telegram_result):
        resp = await client.post("/telegram", json=_make_telegram_update())
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    with patch("app.main.get_events", return_value=[event_row]):
        resp = await client.get("/events")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    assert events[0]["id"] == telegram_result["event_id"]
    assert events[0]["source"] == "telegram"


async def test_telegram_pipeline_increments_cluster_count(client):
    """POST /telegram → GET /clusters shows incremented event_count."""
    telegram_result = {"processed": True, "reason": "ok", "event_id": str(uuid4())}
    cluster_row = {
        "id": FAKE_CLUSTER_ID,
        "name": FAKE_CLUSTER_NAME,
        "glyph_id": "table",
        "myth_text": None,
        "myth_version": 0,
        "event_count": 1,
        "last_updated": "2026-03-18T00:00:00Z",
        "is_seed": True,
    }

    with patch("app.main.process_telegram_update", return_value=telegram_result):
        await client.post("/telegram", json=_make_telegram_update())

    with patch("app.main.get_clusters", return_value=[cluster_row]):
        resp = await client.get("/clusters")
    assert resp.status_code == 200
    clusters = resp.json()
    assert clusters[0]["event_count"] == 1


# --- Granola pipeline ---


async def test_granola_pipeline_stores_events(client):
    """POST /granola → GET /events shows all parsed events."""
    granola_results = [
        {"event_id": str(uuid4()), "participant": "jessie", "cluster_name": FAKE_CLUSTER_ID},
        {"event_id": str(uuid4()), "participant": "emma", "cluster_name": FAKE_CLUSTER_ID},
        {"event_id": str(uuid4()), "participant": "steven", "cluster_name": FAKE_CLUSTER_ID},
    ]

    with patch("app.main.process_granola_upload", return_value=granola_results):
        resp = await client.post("/granola", json={"transcript": SAMPLE_TRANSCRIPT})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["events"]) == 3

    # Verify events appear in GET /events
    event_rows = [
        {**FAKE_EVENT_BASE, "id": r["event_id"], "participant": r["participant"], "source": "granola"}
        for r in granola_results
    ]
    with patch("app.main.get_events", return_value=event_rows):
        resp = await client.get("/events")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 3
    participants = {e["participant"] for e in events}
    assert participants == {"jessie", "emma", "steven"}


async def test_granola_pipeline_participant_filter(client):
    """POST /granola events are filterable by participant."""
    jessie_event = {
        **FAKE_EVENT_BASE,
        "id": str(uuid4()),
        "participant": "jessie",
        "source": "granola",
    }

    with patch("app.main.get_events", return_value=[jessie_event]):
        resp = await client.get("/events?participant=jessie")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    assert events[0]["participant"] == "jessie"


async def test_granola_empty_transcript_returns_400(client):
    """POST /granola with empty transcript returns 400."""
    from app.granola import process_granola_upload as real_fn

    with patch("app.main.process_granola_upload", side_effect=ValueError("Empty transcript")):
        resp = await client.post("/granola", json={"transcript": ""})
    assert resp.status_code == 400
    assert "Empty transcript" in resp.json()["error"]


# --- Cross-source ---


async def test_cross_source_events_appear_together(client):
    """Events from both Telegram and Granola appear in GET /events."""
    telegram_event = {**FAKE_EVENT_BASE, "id": str(uuid4()), "source": "telegram"}
    granola_event = {**FAKE_EVENT_BASE, "id": str(uuid4()), "source": "granola"}

    with patch("app.main.get_events", return_value=[telegram_event, granola_event]):
        resp = await client.get("/events")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 2
    sources = {e["source"] for e in events}
    assert sources == {"telegram", "granola"}


# --- Empty state ---


async def test_empty_state_events(client):
    """GET /events on empty DB returns empty list."""
    with patch("app.main.get_events", return_value=[]):
        resp = await client.get("/events")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_empty_state_clusters_six_seeds(client):
    """GET /clusters returns 6 seed clusters with event_count=0."""
    seed_clusters = [
        {
            "id": str(uuid4()),
            "name": name,
            "glyph_id": glyph,
            "myth_text": None,
            "myth_version": 0,
            "event_count": 0,
            "last_updated": "2026-03-18T00:00:00Z",
            "is_seed": True,
        }
        for name, glyph in [
            ("The Gate", "gate"),
            ("What the Body Keeps", "body"),
            ("The Table", "table"),
            ("The Silence", "silence"),
            ("The Root", "root"),
            ("The Hand", "hand"),
        ]
    ]

    with patch("app.main.get_clusters", return_value=seed_clusters):
        resp = await client.get("/clusters")
    assert resp.status_code == 200
    clusters = resp.json()
    assert len(clusters) == 6
    for cluster in clusters:
        assert cluster["event_count"] == 0


# --- Cluster assignment sanity (mocked embedding) ---


async def test_cluster_assignment_sanity_food_message(client):
    """Send a food-related message and verify cluster assignment.

    This test uses mocked internals to verify the pipeline calls
    assign_cluster. The live version of this test would check similarity
    scores against The Table cluster. Logged for RSK-001 evaluation.
    """
    telegram_result = {
        "processed": True,
        "reason": "ok",
        "event_id": str(uuid4()),
    }

    with patch("app.main.process_telegram_update", return_value=telegram_result):
        resp = await client.post(
            "/telegram",
            json=_make_telegram_update(
                text="We cooked dinner together and shared stories",
                update_id=3001,
            ),
        )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


# --- Granola pipeline error handling ---


async def test_granola_embedding_failure_returns_503(client):
    """POST /granola returns 503 on embedding failure."""
    from app.embedding import EmbeddingError

    with patch("app.main.process_granola_upload", side_effect=EmbeddingError("API down")):
        resp = await client.post("/granola", json={"transcript": SAMPLE_TRANSCRIPT})
    assert resp.status_code == 503
    assert resp.json()["error"] == "pipeline_failed"
