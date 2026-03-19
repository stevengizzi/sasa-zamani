"""Tests for GET /events, GET /clusters, and GET /health endpoints."""

from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models import ClusterResponse, EventResponse

pytestmark = pytest.mark.anyio

FAKE_EVENT = {
    "id": str(uuid4()),
    "label": "morning walk",
    "note": "walked through the park",
    "participant": "jessie",
    "source": "telegram",
    "cluster_id": None,
    "created_at": "2026-03-18T00:00:00Z",
    "event_date": None,
    "xs": None,
    "day": None,
}

FAKE_CLUSTER = {
    "id": str(uuid4()),
    "name": "The Gate",
    "glyph_id": None,
    "myth_text": None,
    "myth_version": 0,
    "event_count": 3,
    "last_updated": "2026-03-18T00:00:00Z",
    "is_seed": True,
}


# --- GET /events ---


async def test_get_events_returns_200_empty(client):
    with patch("app.main.get_events", return_value=[]):
        response = await client.get("/events")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_events_returns_correct_structure(client):
    with patch("app.main.get_events", return_value=[FAKE_EVENT]):
        response = await client.get("/events")
    data = response.json()
    assert len(data) == 1
    event = data[0]
    assert "id" in event
    assert "label" in event
    assert "participant" in event
    assert "source" in event
    assert "created_at" in event
    assert "embedding" not in event


async def test_get_events_filters_by_participant(client):
    with patch("app.main.get_events", return_value=[FAKE_EVENT]) as mock_get:
        response = await client.get("/events?participant=jessie")
    assert response.status_code == 200
    mock_get.assert_called_once_with("jessie")


async def test_get_events_participant_filter_case_insensitive(client):
    with patch("app.main.get_events", return_value=[FAKE_EVENT]) as mock_get:
        response = await client.get("/events?participant=Jessie")
    assert response.status_code == 200
    mock_get.assert_called_once_with("Jessie")


async def test_get_events_nonexistent_participant_returns_empty(client):
    with patch("app.main.get_events", return_value=[]):
        response = await client.get("/events?participant=nonexistent")
    assert response.status_code == 200
    assert response.json() == []


# --- GET /clusters ---


async def test_get_clusters_returns_200(client):
    with patch("app.main.get_clusters", return_value=[FAKE_CLUSTER]):
        response = await client.get("/clusters")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


async def test_get_clusters_correct_structure(client):
    with patch("app.main.get_clusters", return_value=[FAKE_CLUSTER]):
        response = await client.get("/clusters")
    cluster = response.json()[0]
    assert "id" in cluster
    assert "name" in cluster
    assert "event_count" in cluster
    assert "centroid_embedding" not in cluster
    assert "centroid" not in cluster


# --- GET /health ---


async def test_health_returns_health_response_format(client):
    response = await client.get("/health")
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


# --- Model validation ---


def test_event_response_validates():
    event = EventResponse(
        id=uuid4(),
        label="test",
        note=None,
        participant="steven",
        cluster_id=None,
        created_at="2026-03-18T00:00:00Z",
        source="telegram",
    )
    assert event.label == "test"
    assert event.note is None


def test_cluster_response_validates():
    cluster = ClusterResponse(
        id=uuid4(),
        name="The Gate",
        event_count=5,
    )
    assert cluster.name == "The Gate"
    assert cluster.event_count == 5


# --- New model fields (Sprint 2 S1) ---


def test_event_response_serializes_xs_and_day():
    event = EventResponse(
        id=uuid4(),
        label="test",
        note=None,
        participant="steven",
        cluster_id=None,
        created_at="2026-03-18T00:00:00Z",
        source="telegram",
        xs=0.35,
        day=7,
    )
    data = event.model_dump()
    assert data["xs"] == 0.35
    assert data["day"] == 7


def test_event_response_xs_day_default_none():
    event = EventResponse(
        id=uuid4(),
        label="test",
        note=None,
        participant="steven",
        cluster_id=None,
        created_at="2026-03-18T00:00:00Z",
        source="telegram",
    )
    assert event.xs is None
    assert event.day is None


def test_cluster_response_serializes_new_fields():
    cluster = ClusterResponse(
        id=uuid4(),
        name="The Gate",
        event_count=5,
        glyph_id="gate",
        myth_text="The door remembers who passed through.",
        is_seed=True,
    )
    data = cluster.model_dump()
    assert data["glyph_id"] == "gate"
    assert data["myth_text"] == "The door remembers who passed through."
    assert data["is_seed"] is True


def test_cluster_response_new_fields_default():
    cluster = ClusterResponse(
        id=uuid4(),
        name="The Gate",
        event_count=5,
    )
    assert cluster.glyph_id is None
    assert cluster.myth_text is None
    assert cluster.is_seed is False
