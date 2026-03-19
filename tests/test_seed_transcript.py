"""Tests for scripts/seed_transcript.py segmentation, filtering, and pipeline."""

from unittest.mock import patch
from uuid import uuid4

import pytest

from app.embedding import EmbeddingError
from app.segmentation import Segment
from scripts.seed_transcript import (
    filter_by_length,
    main,
)

FAKE_EMBEDDING = [0.1] * 1536
FAKE_CLUSTER_ID = str(uuid4())
FAKE_EVENT_ID = str(uuid4())

LONG_TEXT_A = (
    "This is a long enough segment from speaker A that should"
    " definitely pass the minimum length filter we have configured at one hundred characters."
)
LONG_TEXT_C = (
    "Another sufficiently long segment from speaker C that also exceeds"
    " the minimum character length threshold of one hundred characters easily."
)

FAKE_SEGMENTS_MIXED = [
    Segment(text=LONG_TEXT_A, label="Speaker A long segment", participants=["steven"]),
    Segment(text="Short.", label="Short remark", participants=["emma"]),
    Segment(text=LONG_TEXT_C, label="Speaker C long segment", participants=["jessie"]),
]

FAKE_SEGMENTS_SINGLE = [
    Segment(text=LONG_TEXT_A, label="Speaker A long segment", participants=["steven"]),
]

SPEAKER_MAP = {"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}


def test_min_length_filter_excludes_short():
    segments = [Segment(text="Yeah.", label="Short", participants=["shared"])]
    filtered = filter_by_length(segments, 100)
    assert len(filtered) == 0


def test_min_length_filter_includes_long():
    long_text = "x" * 150
    segments = [Segment(text=long_text, label="Long text", participants=["steven"])]
    filtered = filter_by_length(segments, 100)
    assert len(filtered) == 1
    assert filtered[0].text == long_text


@patch("scripts.seed_transcript.insert_event")
@patch("scripts.seed_transcript.embed_text")
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
def test_dry_run_no_api_calls(mock_seg, mock_embed, mock_insert, tmp_path):
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")
    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
        "--date", "2025-03-17",
        "--dry-run",
    ])
    assert mock_embed.call_count == 0
    assert mock_insert.call_count == 0


@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", return_value=FAKE_EMBEDDING)
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_MIXED)
def test_end_to_end_mock_pipeline(
    mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs, tmp_path
):
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}',
        "--date", "2025-03-17",
        "--min-length", "100",
    ])

    # 3 segments from segmentation, but "Short." is < 100 chars → 2 inserted
    assert mock_embed.call_count == 2
    assert mock_insert.call_count == 2

    # Verify correct participants were passed
    participants = [call.kwargs["participant"] for call in mock_insert.call_args_list]
    assert "steven" in participants
    assert "jessie" in participants
    assert "emma" not in participants  # filtered out


@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", side_effect=[EmbeddingError("API down"), FAKE_EMBEDDING])
@patch("scripts.seed_transcript.segment_transcript", return_value=[
    Segment(text="x" * 150, label="First segment", participants=["steven"]),
    Segment(text="y" * 150, label="Second segment", participants=["emma"]),
])
def test_embedding_error_skips_segment(
    mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs, tmp_path
):
    """Individual embedding failure skips that segment, doesn't abort the run."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven", "Speaker B": "emma"}',
        "--date", "2025-03-17",
        "--min-length", "50",
    ])

    # First segment fails embedding, second succeeds → 1 insert
    assert mock_embed.call_count == 2
    assert mock_insert.call_count == 1


@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", return_value=FAKE_EMBEDDING)
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
def test_date_arg_passed_to_insert(
    mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs, tmp_path
):
    """--date value is forwarded to insert_event as event_date."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
        "--date", "2025-03-17",
        "--min-length", "50",
    ])

    assert mock_insert.call_count == 1
    assert mock_insert.call_args.kwargs["event_date"] == "2025-03-17"


# --- New tests: segmentation integration ---


@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", return_value=FAKE_EMBEDDING)
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
def test_seed_uses_segmentation(
    mock_seg, mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs, tmp_path
):
    """segment_transcript is called with transcript text and speaker_map."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
        "--date", "2025-03-17",
        "--min-length", "50",
    ])

    mock_seg.assert_called_once_with("Some transcript text.\n", {"Speaker A": "steven"}, "shared")


@patch("scripts.seed_transcript.insert_event")
@patch("scripts.seed_transcript.embed_text")
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
def test_seed_dry_run_calls_segmentation(mock_seg, mock_embed, mock_insert, tmp_path):
    """Dry-run calls segment_transcript but not insert_event or embed_text."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
        "--date", "2025-03-17",
        "--dry-run",
    ])

    mock_seg.assert_called_once()
    assert mock_embed.call_count == 0
    assert mock_insert.call_count == 0
