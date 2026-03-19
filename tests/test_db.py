"""Tests for database client and CRUD operations (mocked Supabase)."""

from unittest.mock import MagicMock, patch

import pytest

from app.db import (
    check_connection,
    ensure_schema,
    get_cluster_centroids,
    get_cluster_events_notes,
    get_clusters,
    get_events,
    get_raw_input,
    increment_event_count,
    insert_cluster,
    insert_event,
    insert_raw_input,
    reset_client,
    update_cluster_name,
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


async def test_insert_event_stores_xs_when_provided(mock_supabase):
    fake_event = {
        "id": "evt-xs",
        "label": "test xs",
        "note": "test",
        "participant": "steven",
        "source": "telegram",
        "cluster_id": "cl-1",
        "xs": 0.35,
    }
    insert_chain = _chain(mock_supabase, "events").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_event])

    result = insert_event(
        label="test xs",
        note="test",
        participant="steven",
        embedding=[0.1] * 1536,
        source="telegram",
        cluster_id="cl-1",
        xs=0.35,
    )
    assert result["xs"] == 0.35

    # Verify xs was included in the data dict passed to insert
    call_args = _chain(mock_supabase, "events").insert.call_args
    data_dict = call_args[0][0]
    assert data_dict["xs"] == 0.35


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


async def test_insert_event_with_event_date(mock_supabase):
    fake_event = {"id": "evt-date", "label": "dated", "event_date": "2025-03-17"}
    insert_chain = _chain(mock_supabase, "events").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_event])

    insert_event(
        label="dated",
        note="test",
        participant="steven",
        embedding=[0.1] * 1536,
        source="granola",
        event_date="2025-03-17",
    )

    call_args = _chain(mock_supabase, "events").insert.call_args
    data_dict = call_args[0][0]
    assert data_dict["event_date"] == "2025-03-17"


async def test_insert_event_without_event_date(mock_supabase):
    fake_event = {"id": "evt-nodate", "label": "undated", "event_date": None}
    insert_chain = _chain(mock_supabase, "events").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_event])

    insert_event(
        label="undated",
        note="test",
        participant="steven",
        embedding=[0.1] * 1536,
        source="telegram",
    )

    call_args = _chain(mock_supabase, "events").insert.call_args
    data_dict = call_args[0][0]
    assert "event_date" not in data_dict


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


async def test_get_cluster_centroids_parses_string_centroid(mock_supabase):
    """pgvector returns centroids as JSON strings — verify they are parsed to list[float]."""
    centroid_list = [0.5] * 1536
    centroid_string = "[" + ",".join("0.5" for _ in range(1536)) + "]"
    select_chain = _chain(mock_supabase, "clusters").select.return_value
    select_chain.execute.return_value = MagicMock(
        data=[{"id": "cl-str", "centroid": centroid_string}]
    )

    centroids = get_cluster_centroids()
    assert len(centroids) == 1
    cluster_id, emb = centroids[0]
    assert cluster_id == "cl-str"
    assert isinstance(emb, list)
    assert len(emb) == 1536
    assert emb == centroid_list


# --- increment_event_count ---


async def test_increment_event_count(mock_supabase):
    rpc_chain = mock_supabase.rpc.return_value
    rpc_chain.execute.return_value = MagicMock(data=None)

    increment_event_count("cl-1")

    mock_supabase.rpc.assert_called_once_with("increment_event_count", {"cid": "cl-1"})


# --- insert_cluster glyph_id ---


async def test_insert_cluster_with_glyph_id(mock_supabase):
    fake_cluster = {
        "id": "cl-g1",
        "name": "The Gate",
        "glyph_id": "gate",
        "is_seed": True,
        "event_count": 0,
    }
    insert_chain = _chain(mock_supabase, "clusters").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_cluster])

    result = insert_cluster(name="The Gate", centroid_embedding=[0.5] * 1536, is_seed=True, glyph_id="gate")
    assert result["glyph_id"] == "gate"

    call_args = _chain(mock_supabase, "clusters").insert.call_args
    data_dict = call_args[0][0]
    assert data_dict["glyph_id"] == "gate"


async def test_insert_cluster_without_glyph_id(mock_supabase):
    fake_cluster = {
        "id": "cl-g2",
        "name": "The Root",
        "glyph_id": None,
        "is_seed": False,
        "event_count": 0,
    }
    insert_chain = _chain(mock_supabase, "clusters").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_cluster])

    result = insert_cluster(name="The Root", centroid_embedding=[0.5] * 1536)
    assert result["glyph_id"] is None

    call_args = _chain(mock_supabase, "clusters").insert.call_args
    data_dict = call_args[0][0]
    assert "glyph_id" not in data_dict


# --- atomic increment ---


async def test_increment_event_count_atomic(mock_supabase):
    rpc_chain = mock_supabase.rpc.return_value
    rpc_chain.execute.return_value = MagicMock(data=None)

    increment_event_count("cl-atomic")

    mock_supabase.rpc.assert_called_once_with("increment_event_count", {"cid": "cl-atomic"})
    # Verify no select+update pattern (atomic via RPC)
    _chain(mock_supabase, "clusters").select.assert_not_called()


async def test_increment_event_count_from_zero(mock_supabase):
    rpc_chain = mock_supabase.rpc.return_value
    rpc_chain.execute.return_value = MagicMock(data=None)

    increment_event_count("cl-zero")

    mock_supabase.rpc.assert_called_once_with("increment_event_count", {"cid": "cl-zero"})


# --- participants ---


async def test_insert_event_with_participants(mock_supabase):
    fake_event = {"id": "evt-part", "label": "collab", "participants": ["steven", "emma"]}
    insert_chain = _chain(mock_supabase, "events").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_event])

    insert_event(
        label="collab",
        note="paired session",
        participant="steven",
        embedding=[0.1] * 1536,
        source="granola",
        participants=["steven", "emma"],
    )

    call_args = _chain(mock_supabase, "events").insert.call_args
    data_dict = call_args[0][0]
    assert data_dict["participants"] == ["steven", "emma"]


async def test_insert_event_without_participants(mock_supabase):
    fake_event = {"id": "evt-nopart", "label": "solo", "participants": None}
    insert_chain = _chain(mock_supabase, "events").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_event])

    insert_event(
        label="solo",
        note="solo entry",
        participant="steven",
        embedding=[0.1] * 1536,
        source="telegram",
    )

    call_args = _chain(mock_supabase, "events").insert.call_args
    data_dict = call_args[0][0]
    assert "participants" not in data_dict


async def test_event_response_includes_participants():
    from app.models import EventResponse

    event = EventResponse(
        id="00000000-0000-0000-0000-000000000001",
        label="test",
        note="test note",
        participant="steven",
        cluster_id=None,
        created_at="2026-03-19T00:00:00Z",
        source="telegram",
        participants=["steven", "emma"],
    )
    data = event.model_dump()
    assert data["participants"] == ["steven", "emma"]


# --- insert_raw_input / get_raw_input ---


async def test_insert_raw_input_returns_full_row(mock_supabase):
    fake_row = {
        "id": "ri-1",
        "text": "full transcript text",
        "source": "granola",
        "source_metadata": {"filename": "session.md"},
        "created_at": "2026-03-19T00:00:00Z",
    }
    insert_chain = _chain(mock_supabase, "raw_inputs").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_row])

    result = insert_raw_input(
        text="full transcript text",
        source="granola",
        source_metadata={"filename": "session.md"},
    )
    assert result["id"] == "ri-1"
    assert result["text"] == "full transcript text"
    assert result["source"] == "granola"
    assert result["source_metadata"] == {"filename": "session.md"}
    assert result["created_at"] == "2026-03-19T00:00:00Z"


async def test_insert_raw_input_stores_source_metadata_as_jsonb(mock_supabase):
    metadata = {"chat_id": 12345, "username": "steven"}
    fake_row = {"id": "ri-2", "text": "msg", "source": "telegram", "source_metadata": metadata}
    insert_chain = _chain(mock_supabase, "raw_inputs").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_row])

    insert_raw_input(text="msg", source="telegram", source_metadata=metadata)

    call_args = _chain(mock_supabase, "raw_inputs").insert.call_args
    data_dict = call_args[0][0]
    assert data_dict["source_metadata"] == metadata


async def test_insert_raw_input_none_metadata_defaults_to_omitted(mock_supabase):
    fake_row = {"id": "ri-3", "text": "msg", "source": "telegram", "source_metadata": {}}
    insert_chain = _chain(mock_supabase, "raw_inputs").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_row])

    insert_raw_input(text="msg", source="telegram")

    call_args = _chain(mock_supabase, "raw_inputs").insert.call_args
    data_dict = call_args[0][0]
    assert "source_metadata" not in data_dict


async def test_get_raw_input_returns_existing_row(mock_supabase):
    fake_row = {"id": "ri-4", "text": "transcript", "source": "granola", "source_metadata": {}}
    select_chain = _chain(mock_supabase, "raw_inputs").select.return_value
    select_chain.eq.return_value = select_chain
    select_chain.execute.return_value = MagicMock(data=[fake_row])

    result = get_raw_input("ri-4")
    assert result is not None
    assert result["id"] == "ri-4"
    assert result["text"] == "transcript"


async def test_get_raw_input_returns_none_for_missing(mock_supabase):
    select_chain = _chain(mock_supabase, "raw_inputs").select.return_value
    select_chain.eq.return_value = select_chain
    select_chain.execute.return_value = MagicMock(data=[])

    result = get_raw_input("nonexistent-id")
    assert result is None


async def test_insert_event_with_raw_input_fields(mock_supabase):
    fake_event = {
        "id": "evt-ri",
        "label": "segmented",
        "raw_input_id": "ri-1",
        "start_line": 10,
        "end_line": 25,
    }
    insert_chain = _chain(mock_supabase, "events").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_event])

    result = insert_event(
        label="segmented",
        note="from transcript",
        participant="steven",
        embedding=[0.1] * 1536,
        source="granola",
        raw_input_id="ri-1",
        start_line=10,
        end_line=25,
    )
    assert result["raw_input_id"] == "ri-1"
    assert result["start_line"] == 10
    assert result["end_line"] == 25

    call_args = _chain(mock_supabase, "events").insert.call_args
    data_dict = call_args[0][0]
    assert data_dict["raw_input_id"] == "ri-1"
    assert data_dict["start_line"] == 10
    assert data_dict["end_line"] == 25


async def test_insert_event_without_raw_input_fields_backward_compat(mock_supabase):
    fake_event = {"id": "evt-compat", "label": "old style"}
    insert_chain = _chain(mock_supabase, "events").insert.return_value
    insert_chain.execute.return_value = MagicMock(data=[fake_event])

    insert_event(
        label="old style",
        note="no raw input",
        participant="steven",
        embedding=[0.1] * 1536,
        source="telegram",
    )

    call_args = _chain(mock_supabase, "events").insert.call_args
    data_dict = call_args[0][0]
    assert "raw_input_id" not in data_dict
    assert "start_line" not in data_dict
    assert "end_line" not in data_dict


async def test_ensure_schema_probes_raw_inputs(mock_supabase):
    ensure_schema()
    table_calls = [call.args[0] for call in mock_supabase.table.call_args_list]
    assert "raw_inputs" in table_calls


# --- update_cluster_name ---


async def test_update_cluster_name(mock_supabase):
    update_chain = _chain(mock_supabase, "clusters").update.return_value
    update_chain.eq.return_value = update_chain
    update_chain.execute.return_value = MagicMock(data=None)

    update_cluster_name("cl-rename", "The Hearth")

    _chain(mock_supabase, "clusters").update.assert_called_once_with({"name": "The Hearth"})
    update_chain.eq.assert_called_once_with("id", "cl-rename")


# --- get_cluster_events_notes ---


async def test_get_cluster_events_notes_returns_truncated(mock_supabase):
    long_note = "x" * 300
    fake_events = [
        {"note": long_note},
        {"note": "short note"},
    ]
    select_chain = _chain(mock_supabase, "events").select.return_value
    select_chain.eq.return_value = select_chain
    select_chain.execute.return_value = MagicMock(data=fake_events)

    notes = get_cluster_events_notes("cl-notes")
    assert len(notes) == 2
    assert len(notes[0]) == 200
    assert notes[1] == "short note"
