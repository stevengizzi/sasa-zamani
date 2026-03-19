"""Tests for scripts/seed_transcript.py parsing, filtering, and pipeline."""

from unittest.mock import patch
from uuid import uuid4

import pytest

from app.embedding import EmbeddingError
from scripts.seed_transcript import (
    filter_by_length,
    main,
    parse_transcript,
)

FAKE_EMBEDDING = [0.1] * 1536
FAKE_CLUSTER_ID = str(uuid4())
FAKE_EVENT_ID = str(uuid4())

SAMPLE_TRANSCRIPT = (
    "Speaker A: This is a long enough segment from speaker A that should"
    " definitely pass the minimum length filter we have configured at one hundred characters.\n"
    "Speaker B: Short.\n"
    "Speaker C: Another sufficiently long segment from speaker C that also exceeds"
    " the minimum character length threshold of one hundred characters easily."
)

SPEAKER_MAP = {"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}


def test_speaker_remapping_known():
    segments = parse_transcript(
        "Speaker A: Hello world from speaker A.",
        {"Speaker A": "steven"},
        "shared",
    )
    assert len(segments) == 1
    assert segments[0]["participant"] == "steven"


def test_speaker_remapping_unknown_defaults_shared():
    segments = parse_transcript(
        "Speaker D: Hello from an unmapped speaker.",
        {"Speaker A": "steven"},
        "shared",
    )
    assert len(segments) == 1
    assert segments[0]["participant"] == "shared"


def test_min_length_filter_excludes_short():
    segments = [{"text": "Yeah.", "participant": "shared"}]
    filtered = filter_by_length(segments, 100)
    assert len(filtered) == 0


def test_min_length_filter_includes_long():
    long_text = "x" * 150
    segments = [{"text": long_text, "participant": "steven"}]
    filtered = filter_by_length(segments, 100)
    assert len(filtered) == 1
    assert filtered[0]["text"] == long_text


@patch("scripts.seed_transcript.insert_event")
@patch("scripts.seed_transcript.embed_text")
def test_dry_run_no_api_calls(mock_embed, mock_insert, tmp_path):
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text(
        "Speaker A: Some text that is long enough to pass the default filter"
        " threshold of one hundred characters so it will not be excluded.\n"
    )
    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
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
def test_end_to_end_mock_pipeline(
    mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs, tmp_path
):
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text(SAMPLE_TRANSCRIPT)

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}',
        "--min-length", "100",
    ])

    # 3 segments parsed, but "Short." (Speaker B) is < 100 chars → 2 inserted
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
def test_embedding_error_skips_segment(
    mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs, tmp_path
):
    """Individual embedding failure skips that segment, doesn't abort the run."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text(
        "Speaker A: First segment that is long enough to pass the minimum length"
        " filter threshold of one hundred characters for testing purposes.\n"
        "Speaker B: Second segment that is also long enough to pass the minimum"
        " length filter threshold of one hundred characters for testing purposes.\n"
    )

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven", "Speaker B": "emma"}',
        "--min-length", "50",
    ])

    # First segment fails embedding, second succeeds → 1 insert
    assert mock_embed.call_count == 2
    assert mock_insert.call_count == 1
