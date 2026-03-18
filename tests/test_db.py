"""Tests for database client and CRUD operations (mocked Supabase)."""

from unittest.mock import MagicMock, patch

import pytest

from app.db import (
    check_connection,
    ensure_schema,
    get_cluster_centroids,
    get_clusters,
    get_events,
    increment_event_count,
    insert_cluster,
    insert_event,
    reset_client,
)

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def _reset_db_client():
    """Reset the db module singleton before and after each test."""
    reset_client()
    yield
    reset_client()


@pytest.fixture
def mock_supabase():
    """Provide a mocked Supabase client that is injected into app.db."""
    mock_client = MagicMock()
    with patch("app.db.create_client", return_value=mock_client):
        yield mock_client


def _chain(mock_client, table_name):
    """Return the mock chain for a given table (table → select/insert/update → ... → execute)."""
    return mock_client.table(table_name)


# --- check_connection ---


async def test_check_connection_returns_true(mock_supabase):
    assert check_connection() is True


async def test_check_connection_returns_false_on_error(mock_supabase):
    mock_supabase.table.side_effect = Exception("unreachable")
    assert check_connection() is False


# --- ensure_schema ---


async def test_ensure_schema_is_idempotent(mock_supabase):
    """Calling ensure_schema twice should not raise."""
    ensure_schema()
    ensure_schema()
    # Verify it probed all three tables
    table_calls = [call.args[0] for call in mock_supabase.table.call_args_list]
    assert "clusters" in table_calls
    assert "events" in table_calls
    assert "myths" in table_calls


async def test_ensure_schema_raises_on_missing_table(mock_supabase):
    """ensure_schema wraps opaque errors with a clear message."""
    chain = _chain(mock_supabase, "events").select.return_value.limit.return_value
    chain.execute.side_effect = Exception("relation does not exist")

    with pytest.raises(RuntimeError, match="init_supabase.sql"):
        ensure_schema()


# --- insert_event / get_events ---


async def test_insert_event_and_get_events_roundtrip(mock_supabase):
    fake_event = {
        "id": "evt-1",
        "label": "morning walk",
        "note": "walked through the park",
        "participant": "steven",
        "source": "telegram",
        "cluster_id": None,
        "created_at": "2026-03-18T00:00:00Z",
        "event_date": None,
        "xs": None,
        "day": None,
    }
    embedding = [0.1] * 1536

    # Mock insert response
    insert_chain = _chain(mock_supabase, "events").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_event])

    result = insert_event(
        label="morning walk",
        note="walked through the park",
        participant="steven",
        embedding=embedding,
        source="telegram",
    )
    assert result["label"] == "morning walk"
    assert result["participant"] == "steven"

    # Mock get_events response — embedding should NOT be in the returned data
    select_chain = _chain(mock_supabase, "events").select.return_value
    select_chain.execute.return_value = MagicMock(data=[fake_event])

    events = get_events()
    assert len(events) == 1
    assert "embedding" not in events[0]


async def test_get_events_with_participant_filter(mock_supabase):
    fake_events = [
        {"id": "evt-2", "label": "coffee", "participant": "emma"},
    ]
    select_chain = _chain(mock_supabase, "events").select.return_value
    select_chain.ilike.return_value = select_chain
    select_chain.execute.return_value = MagicMock(data=fake_events)

    events = get_events(participant="emma")
    assert len(events) == 1
    assert events[0]["participant"] == "emma"
    # Verify ilike was called for case-insensitive filter
    select_chain.ilike.assert_called_once_with("participant", "emma")


async def test_get_events_returns_empty_list(mock_supabase):
    select_chain = _chain(mock_supabase, "events").select.return_value
    select_chain.execute.return_value = MagicMock(data=[])

    events = get_events()
    assert events == []


# --- insert_cluster / get_clusters ---


async def test_insert_cluster_and_get_clusters_roundtrip(mock_supabase):
    fake_cluster = {
        "id": "cl-1",
        "name": "The Gate",
        "glyph_id": None,
        "myth_text": None,
        "myth_version": 0,
        "event_count": 0,
        "last_updated": "2026-03-18T00:00:00Z",
        "is_seed": True,
    }
    centroid = [0.5] * 1536

    insert_chain = _chain(mock_supabase, "clusters").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_cluster])

    result = insert_cluster(name="The Gate", centroid_embedding=centroid, is_seed=True)
    assert result["name"] == "The Gate"
    assert result["is_seed"] is True

    # get_clusters should not include centroid
    select_chain = _chain(mock_supabase, "clusters").select.return_value
    select_chain.execute.return_value = MagicMock(data=[fake_cluster])

    clusters = get_clusters()
    assert len(clusters) == 1
    assert "centroid" not in clusters[0]


# --- get_cluster_centroids ---


async def test_get_cluster_centroids(mock_supabase):
    centroid = [0.5] * 1536
    select_chain = _chain(mock_supabase, "clusters").select.return_value
    select_chain.execute.return_value = MagicMock(
        data=[{"id": "cl-1", "centroid": centroid}]
    )

    centroids = get_cluster_centroids()
    assert len(centroids) == 1
    cluster_id, emb = centroids[0]
    assert cluster_id == "cl-1"
    assert len(emb) == 1536


# --- increment_event_count ---


async def test_increment_event_count(mock_supabase):
    # Mock the read step
    select_chain = (
        _chain(mock_supabase, "clusters")
        .select.return_value
        .eq.return_value
        .single.return_value
    )
    select_chain.execute.return_value = MagicMock(data={"event_count": 5})

    # Mock the update step
    update_chain = (
        _chain(mock_supabase, "clusters")
        .update.return_value
        .eq.return_value
    )
    update_chain.execute.return_value = MagicMock(data=[{"event_count": 6}])

    increment_event_count("cl-1")

    # Verify update was called with incremented count
    _chain(mock_supabase, "clusters").update.assert_called_with({"event_count": 6})
