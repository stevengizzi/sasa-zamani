"""Tests for scripts/seed_transcript.py segmentation, filtering, and pipeline."""

from unittest.mock import patch, call
from uuid import uuid4

import pytest

from app.embedding import EmbeddingError
from app.segmentation import Segment
from scripts.seed_transcript import main

FAKE_EMBEDDING = [0.1] * 1536
FAKE_CLUSTER_ID = str(uuid4())
FAKE_EVENT_ID = str(uuid4())
FAKE_RAW_INPUT_ID = str(uuid4())

LONG_TEXT_A = (
    "This is a long enough segment from speaker A that should"
    " definitely pass the minimum length filter we have configured at one hundred characters."
)
LONG_TEXT_C = (
    "Another sufficiently long segment from speaker C that also exceeds"
    " the minimum character length threshold of one hundred characters easily."
)

FAKE_SEGMENTS_MIXED = [
    Segment(text=LONG_TEXT_A, label="Speaker A long segment", participants=["steven"], significance=0.8),
    Segment(text="Short.", label="Short remark", participants=["emma"], significance=0.1),
    Segment(text=LONG_TEXT_C, label="Speaker C long segment", participants=["jessie"], significance=0.7),
]

FAKE_SEGMENTS_SINGLE = [
    Segment(text=LONG_TEXT_A, label="Speaker A long segment", participants=["steven"], significance=0.8),
]

SPEAKER_MAP = {"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}


def _settings_patch():
    """Return a mock Settings with significance_threshold=0.3."""
    from unittest.mock import MagicMock
    settings = MagicMock()
    settings.significance_threshold = 0.3
    settings.cluster_join_threshold = 0.3
    settings.archetype_naming_threshold = 3
    return settings


@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.insert_event")
@patch("scripts.seed_transcript.embed_text")
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
def test_dry_run_no_api_calls(mock_seg, mock_embed, mock_insert, mock_settings, tmp_path):
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


@patch("scripts.seed_transcript.maybe_name_cluster")
@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", return_value=FAKE_EMBEDDING)
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_MIXED)
@patch("scripts.seed_transcript.insert_raw_input", return_value={"id": FAKE_RAW_INPUT_ID})
@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.assign_or_create_cluster", return_value=(FAKE_CLUSTER_ID, 0.85, False))
def test_end_to_end_mock_pipeline(
    mock_assign, mock_settings, mock_raw, mock_seg, mock_embed, mock_centroids,
    mock_insert, mock_incr, mock_cluster, mock_xs, mock_name, tmp_path
):
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}',
        "--date", "2025-03-17",
    ])

    # 3 segments, "Short remark" has sig=0.1 < 0.3 threshold → 2 inserted
    assert mock_embed.call_count == 2
    assert mock_insert.call_count == 2

    # Verify correct participants were passed
    participants = [call.kwargs["participant"] for call in mock_insert.call_args_list]
    assert "steven" in participants
    assert "jessie" in participants
    assert "emma" not in participants  # filtered out by significance


@patch("scripts.seed_transcript.maybe_name_cluster")
@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", side_effect=[EmbeddingError("API down"), FAKE_EMBEDDING])
@patch("scripts.seed_transcript.segment_transcript", return_value=[
    Segment(text="x" * 150, label="First segment", participants=["steven"], significance=0.9),
    Segment(text="y" * 150, label="Second segment", participants=["emma"], significance=0.9),
])
@patch("scripts.seed_transcript.insert_raw_input", return_value={"id": FAKE_RAW_INPUT_ID})
@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.assign_or_create_cluster", return_value=(FAKE_CLUSTER_ID, 0.85, False))
def test_embedding_error_skips_segment(
    mock_assign, mock_settings, mock_raw, mock_seg, mock_embed, mock_centroids,
    mock_insert, mock_incr, mock_cluster, mock_xs, mock_name, tmp_path
):
    """Individual embedding failure skips that segment, doesn't abort the run."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven", "Speaker B": "emma"}',
        "--date", "2025-03-17",
    ])

    # First segment fails embedding, second succeeds → 1 insert
    assert mock_embed.call_count == 2
    assert mock_insert.call_count == 1


@patch("scripts.seed_transcript.maybe_name_cluster")
@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", return_value=FAKE_EMBEDDING)
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
@patch("scripts.seed_transcript.insert_raw_input", return_value={"id": FAKE_RAW_INPUT_ID})
@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.assign_or_create_cluster", return_value=(FAKE_CLUSTER_ID, 0.85, False))
def test_date_arg_passed_to_insert(
    mock_assign, mock_settings, mock_raw, mock_seg, mock_embed, mock_centroids,
    mock_insert, mock_incr, mock_cluster, mock_xs, mock_name, tmp_path
):
    """--date value is forwarded to insert_event as event_date."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
        "--date", "2025-03-17",
    ])

    assert mock_insert.call_count == 1
    assert mock_insert.call_args.kwargs["event_date"] == "2025-03-17"


# --- Segmentation integration ---


@patch("scripts.seed_transcript.maybe_name_cluster")
@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", return_value=FAKE_EMBEDDING)
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
@patch("scripts.seed_transcript.insert_raw_input", return_value={"id": FAKE_RAW_INPUT_ID})
@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.assign_or_create_cluster", return_value=(FAKE_CLUSTER_ID, 0.85, False))
def test_seed_uses_segmentation(
    mock_assign, mock_settings, mock_raw, mock_seg, mock_embed, mock_centroids,
    mock_insert, mock_incr, mock_cluster, mock_xs, mock_name, tmp_path
):
    """segment_transcript is called with transcript text and speaker_map."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
        "--date", "2025-03-17",
    ])

    mock_seg.assert_called_once_with("Some transcript text.\n", {"Speaker A": "steven"}, "shared")


@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.insert_event")
@patch("scripts.seed_transcript.embed_text")
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
def test_seed_dry_run_calls_segmentation(mock_seg, mock_embed, mock_insert, mock_settings, tmp_path):
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


# --- New Session 4b tests ---


@patch("scripts.seed_transcript.maybe_name_cluster")
@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", return_value=FAKE_EMBEDDING)
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
@patch("scripts.seed_transcript.insert_raw_input", return_value={"id": FAKE_RAW_INPUT_ID})
@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.assign_or_create_cluster", return_value=(FAKE_CLUSTER_ID, 0.85, False))
def test_run_pipeline_stores_raw_input_before_processing(
    mock_assign, mock_settings, mock_raw, mock_seg, mock_embed, mock_centroids,
    mock_insert, mock_incr, mock_cluster, mock_xs, mock_name, tmp_path
):
    """run_pipeline stores transcript in raw_inputs before processing segments."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
        "--date", "2025-03-17",
    ])

    mock_raw.assert_called_once()
    assert mock_raw.call_args.kwargs["source"] == "granola"
    assert mock_raw.call_args.kwargs["text"] == "Some transcript text.\n"
    # raw_input_id passed to insert_event
    assert mock_insert.call_args.kwargs["raw_input_id"] == FAKE_RAW_INPUT_ID


@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.dedup_labels", wraps=lambda segs: segs)
@patch("scripts.seed_transcript.insert_event")
@patch("scripts.seed_transcript.embed_text")
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
def test_run_pipeline_calls_dedup_labels(mock_seg, mock_embed, mock_insert, mock_dedup, mock_settings, tmp_path):
    """main() calls dedup_labels on segments."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
        "--date", "2025-03-17",
        "--dry-run",
    ])

    mock_dedup.assert_called_once()


@patch("scripts.seed_transcript.maybe_name_cluster")
@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", return_value=FAKE_EMBEDDING)
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_MIXED)
@patch("scripts.seed_transcript.insert_raw_input", return_value={"id": FAKE_RAW_INPUT_ID})
@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.assign_or_create_cluster", return_value=(FAKE_CLUSTER_ID, 0.85, False))
def test_filters_by_significance_not_length(
    mock_assign, mock_settings, mock_raw, mock_seg, mock_embed, mock_centroids,
    mock_insert, mock_incr, mock_cluster, mock_xs, mock_name, tmp_path
):
    """Significance filtering replaces min-length: low-sig segments are excluded."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}',
        "--date", "2025-03-17",
    ])

    # FAKE_SEGMENTS_MIXED: sig 0.8, 0.1, 0.7 — threshold 0.3 → 0.1 filtered
    assert mock_embed.call_count == 2
    assert mock_insert.call_count == 2


@patch("scripts.seed_transcript.maybe_name_cluster")
@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", return_value=FAKE_EMBEDDING)
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
@patch("scripts.seed_transcript.insert_raw_input", return_value={"id": FAKE_RAW_INPUT_ID})
@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.assign_or_create_cluster", return_value=(FAKE_CLUSTER_ID, 0.85, False))
def test_run_pipeline_uses_assign_or_create_cluster(
    mock_assign, mock_settings, mock_raw, mock_seg, mock_embed, mock_centroids,
    mock_insert, mock_incr, mock_cluster, mock_xs, mock_name, tmp_path
):
    """run_pipeline uses assign_or_create_cluster instead of assign_cluster."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
        "--date", "2025-03-17",
    ])

    mock_assign.assert_called_once()


NEW_CLUSTER_ID = str(uuid4())


@patch("scripts.seed_transcript.maybe_name_cluster")
@patch("scripts.seed_transcript.update_event_xs")
@patch("scripts.seed_transcript.get_cluster_by_id", return_value={"name": "The Unnamed", "event_count": 1})
@patch("scripts.seed_transcript.increment_event_count")
@patch("scripts.seed_transcript.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("scripts.seed_transcript.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("scripts.seed_transcript.embed_text", return_value=FAKE_EMBEDDING)
@patch("scripts.seed_transcript.segment_transcript", return_value=FAKE_SEGMENTS_SINGLE)
@patch("scripts.seed_transcript.insert_raw_input", return_value={"id": FAKE_RAW_INPUT_ID})
@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.assign_or_create_cluster", return_value=(NEW_CLUSTER_ID, 0.15, True))
def test_run_pipeline_refreshes_centroids_on_new_cluster(
    mock_assign, mock_settings, mock_raw, mock_seg, mock_embed, mock_centroids,
    mock_insert, mock_incr, mock_cluster, mock_xs, mock_name, tmp_path
):
    """When assign_or_create_cluster returns created=True, centroids are refreshed."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven"}',
        "--date", "2025-03-17",
    ])

    # Initial call + 1 refresh after creation
    assert mock_centroids.call_count == 2


@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.segment_transcript", return_value=[
    Segment(text="High sig content", label="Important topic", participants=["steven"], significance=0.9),
    Segment(text="Low sig content", label="Just logistics", participants=["emma"], significance=0.1),
])
def test_print_dry_run_shows_significance_scores(mock_seg, mock_settings, tmp_path, capsys):
    """Dry-run output includes significance scores for all segments."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven", "Speaker B": "emma"}',
        "--date", "2025-03-17",
        "--dry-run",
    ])

    captured = capsys.readouterr().out
    assert "(sig=0.90)" in captured
    assert "(sig=0.10)" in captured


@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.segment_transcript", return_value=[
    Segment(text="High sig content", label="Important topic", participants=["steven"], significance=0.9),
    Segment(text="Low sig content", label="Just logistics", participants=["emma"], significance=0.1),
])
def test_print_dry_run_marks_filtered_segments(mock_seg, mock_settings, tmp_path, capsys):
    """Dry-run output marks below-threshold segments with [FILTERED]."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven", "Speaker B": "emma"}',
        "--date", "2025-03-17",
        "--dry-run",
    ])

    captured = capsys.readouterr().out
    assert "[FILTERED]" in captured
    # The high-sig segment should NOT be marked filtered
    lines = captured.split("\n")
    important_line = [l for l in lines if "Important topic" in l][0]
    logistics_line = [l for l in lines if "Just logistics" in l][0]
    assert "[FILTERED]" not in important_line
    assert "[FILTERED]" in logistics_line


def test_min_length_arg_removed():
    """--min-length arg no longer accepted by parse_args."""
    from scripts.seed_transcript import parse_args

    with pytest.raises(SystemExit):
        parse_args([
            "--file", "test.md",
            "--speaker-map", '{}',
            "--date", "2025-01-01",
            "--min-length", "100",
        ])


@patch("scripts.seed_transcript.get_settings", side_effect=lambda: _settings_patch())
@patch("scripts.seed_transcript.segment_transcript", return_value=[
    Segment(text="Content A", label="Topic A", participants=["steven"], significance=0.5),
    Segment(text="Content B", label="Topic B", participants=["emma"], significance=0.2),
])
def test_print_dry_run_summary_count(mock_seg, mock_settings, tmp_path, capsys):
    """Dry-run output shows 'Segments above significance threshold: N / M'."""
    transcript_file = tmp_path / "transcript.md"
    transcript_file.write_text("Some transcript text.\n")

    main([
        "--file", str(transcript_file),
        "--speaker-map", '{"Speaker A": "steven", "Speaker B": "emma"}',
        "--date", "2025-03-17",
        "--dry-run",
    ])

    captured = capsys.readouterr().out
    assert "Segments above significance threshold: 1 / 2" in captured
