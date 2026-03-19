"""Tests for Granola transcript processor and pipeline."""

from unittest.mock import patch
from uuid import uuid4

import pytest

from app.embedding import EmbeddingError
from app.granola import SPEAKER_MAP, process_granola_upload
from app.segmentation import Segment, SegmentationError

FAKE_EMBEDDING = [0.1] * 1536
FAKE_CLUSTER_ID = str(uuid4())
FAKE_EVENT_ID = str(uuid4())

SAMPLE_TRANSCRIPT = (
    "Jessie: I had the strangest dream last night about crossing a bridge"
    " that kept extending.\n\n"
    "Emma: That reminds me of the conversation we had about thresholds."
    " The food was incredible at that dinner, by the way.\n\n"
    "Steven: I've been writing about exactly this — the way memory reshapes"
    " when you try to pin it down."
)

FAKE_SEGMENTS = [
    Segment(text="Dream about crossing a bridge", label="Bridge crossing dream", participants=["jessie"]),
    Segment(text="Conversation about thresholds", label="Threshold conversation", participants=["emma"]),
    Segment(text="Memory reshaping when pinned", label="Memory reshaping reflection", participants=["steven"]),
]


# --- SPEAKER_MAP ---


def test_speaker_map_contains_all_participants():
    assert "Jessie" in SPEAKER_MAP
    assert "Emma" in SPEAKER_MAP
    assert "Steven" in SPEAKER_MAP
    assert SPEAKER_MAP["Jessie"] == "jessie"
    assert SPEAKER_MAP["Emma"] == "emma"
    assert SPEAKER_MAP["Steven"] == "steven"


# --- process_granola_upload ---


@patch("app.granola.update_event_xs")
@patch("app.granola.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.granola.increment_event_count")
@patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.granola.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.granola.segment_transcript", return_value=FAKE_SEGMENTS)
def test_process_granola_stores_correct_count(mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    results = process_granola_upload(SAMPLE_TRANSCRIPT)
    assert len(results) == 3
    assert mock_embed.call_count == 3
    assert mock_insert.call_count == 3
    assert mock_incr.call_count == 3
    for result in results:
        assert result["event_id"] == FAKE_EVENT_ID


@patch("app.granola.update_event_xs")
@patch("app.granola.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.granola.increment_event_count")
@patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.granola.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.granola.segment_transcript", return_value=FAKE_SEGMENTS)
def test_process_granola_source_is_granola(mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    process_granola_upload(SAMPLE_TRANSCRIPT)
    for call in mock_insert.call_args_list:
        assert call.kwargs["source"] == "granola"


@patch("app.granola.update_event_xs")
@patch("app.granola.get_cluster_by_id", return_value={"name": "The Root", "event_count": 2})
@patch("app.granola.increment_event_count")
@patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.granola.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.granola.segment_transcript", return_value=FAKE_SEGMENTS)
def test_process_granola_computes_xs_for_each_segment(mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    results = process_granola_upload(SAMPLE_TRANSCRIPT)
    assert mock_xs.call_count == 3
    for call in mock_xs.call_args_list:
        xs_value = call[0][1]
        assert 0.0 <= xs_value <= 1.0


def test_process_granola_empty_raises():
    with pytest.raises(ValueError, match="Empty transcript"):
        process_granola_upload("")


@patch("app.granola.segment_transcript", return_value=FAKE_SEGMENTS[:1])
@patch("app.granola.embed_text", side_effect=EmbeddingError("API down"))
def test_process_granola_embedding_failure_no_partial_write(mock_embed, mock_seg):
    with pytest.raises(EmbeddingError):
        process_granola_upload(SAMPLE_TRANSCRIPT)


@patch("app.granola.update_event_xs")
@patch("app.granola.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.granola.increment_event_count")
@patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.granola.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.granola.segment_transcript", return_value=FAKE_SEGMENTS)
def test_granola_return_contract_cluster_name(mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    results = process_granola_upload(SAMPLE_TRANSCRIPT)
    for result in results:
        assert result["cluster_name"] == "The Gate"
        assert "-" not in result["cluster_name"] or len(result["cluster_name"]) != 36


@patch("app.granola.update_event_xs")
@patch("app.granola.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.granola.increment_event_count", side_effect=RuntimeError("RPC failed"))
@patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.granola.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.granola.segment_transcript", return_value=FAKE_SEGMENTS)
def test_granola_increment_failure_event_survives(mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    results = process_granola_upload(SAMPLE_TRANSCRIPT)
    assert len(results) == 3
    for result in results:
        assert result["event_id"] == FAKE_EVENT_ID
        assert result["cluster_name"] == "The Gate"


# --- New tests: segmentation integration ---


@patch("app.granola.update_event_xs")
@patch("app.granola.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.granola.increment_event_count")
@patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.granola.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.granola.segment_transcript", return_value=FAKE_SEGMENTS)
def test_granola_uses_segmentation(mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    """segment_transcript is called with transcript text and speaker_map."""
    process_granola_upload(SAMPLE_TRANSCRIPT)
    mock_seg.assert_called_once_with(SAMPLE_TRANSCRIPT, SPEAKER_MAP, "shared")


@patch("app.granola.update_event_xs")
@patch("app.granola.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.granola.increment_event_count")
@patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.granola.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.granola.segment_transcript", return_value=[
    Segment(text="Shared discussion topic", label="Shared topic", participants=["steven", "emma"]),
])
def test_granola_multi_speaker_sets_shared(mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    """Multi-speaker segment produces participant='shared' with full participants array."""
    results = process_granola_upload(SAMPLE_TRANSCRIPT)
    assert len(results) == 1
    assert results[0]["participant"] == "shared"
    assert mock_insert.call_args.kwargs["participant"] == "shared"
    assert mock_insert.call_args.kwargs["participants"] == ["steven", "emma"]


@patch("app.granola.update_event_xs")
@patch("app.granola.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.granola.increment_event_count")
@patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.granola.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.granola.segment_transcript", return_value=[
    Segment(text="Steven solo thought", label="Solo thought", participants=["steven"]),
])
def test_granola_single_speaker_sets_name(mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    """Single-speaker segment uses that speaker's name as participant."""
    results = process_granola_upload(SAMPLE_TRANSCRIPT)
    assert len(results) == 1
    assert results[0]["participant"] == "steven"
    assert mock_insert.call_args.kwargs["participant"] == "steven"
    assert mock_insert.call_args.kwargs["participants"] == ["steven"]


def test_granola_segmentation_error_propagates():
    """SegmentationError from segment_transcript propagates (no silent fallback)."""
    with patch("app.granola.segment_transcript", side_effect=SegmentationError("LLM failed")):
        with pytest.raises(SegmentationError, match="LLM failed"):
            process_granola_upload(SAMPLE_TRANSCRIPT)


@patch("app.granola.update_event_xs")
@patch("app.granola.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("app.granola.increment_event_count")
@patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.granola.embed_text", return_value=FAKE_EMBEDDING)
@patch("app.granola.segment_transcript", return_value=FAKE_SEGMENTS)
def test_granola_labels_from_segmentation(mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    """Labels come from segment.label, not text[:80]."""
    process_granola_upload(SAMPLE_TRANSCRIPT)
    labels = [call.kwargs["label"] for call in mock_insert.call_args_list]
    assert labels == ["Bridge crossing dream", "Threshold conversation", "Memory reshaping reflection"]
