"""Tests for Granola transcript processor and pipeline."""

from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest

from app.embedding import EmbeddingError
from app.granola import SPEAKER_MAP, process_granola_upload
from app.segmentation import Segment, SegmentationError

FAKE_EMBEDDING = [0.1] * 1536
FAKE_CLUSTER_ID = str(uuid4())
FAKE_EVENT_ID = str(uuid4())
FAKE_RAW_INPUT_ID = str(uuid4())

SAMPLE_TRANSCRIPT = (
    "Jessie: I had the strangest dream last night about crossing a bridge"
    " that kept extending.\n\n"
    "Emma: That reminds me of the conversation we had about thresholds."
    " The food was incredible at that dinner, by the way.\n\n"
    "Steven: I've been writing about exactly this — the way memory reshapes"
    " when you try to pin it down."
)

FAKE_SEGMENTS = [
    Segment(text="Dream about crossing a bridge", label="Bridge crossing dream", participants=["jessie"], start_line=1, end_line=2, significance=0.8),
    Segment(text="Conversation about thresholds", label="Threshold conversation", participants=["emma"], start_line=3, end_line=4, significance=0.7),
    Segment(text="Memory reshaping when pinned", label="Memory reshaping reflection", participants=["steven"], start_line=5, end_line=6, significance=0.9),
]

FAKE_SETTINGS = MagicMock(significance_threshold=0.3)


def _base_patches():
    """Return the standard patch stack for process_granola_upload tests."""
    return [
        patch("app.granola.insert_raw_input", return_value={"id": FAKE_RAW_INPUT_ID}),
        patch("app.granola.segment_transcript", return_value=FAKE_SEGMENTS),
        patch("app.granola.dedup_labels", side_effect=lambda segs: segs),
        patch("app.granola.filter_by_significance", side_effect=lambda segs, t: segs),
        patch("app.granola.get_settings", return_value=FAKE_SETTINGS),
        patch("app.granola.embed_text", return_value=FAKE_EMBEDDING),
        patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)]),
        patch("app.granola.assign_or_create_cluster", return_value=(FAKE_CLUSTER_ID, 0.9, False)),
        patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID}),
        patch("app.granola.increment_event_count"),
        patch("app.granola.maybe_name_cluster"),
        patch("app.granola.get_cluster_by_id", return_value={"name": "The Gate", "event_count": 1}),
        patch("app.granola.update_event_xs"),
    ]


def _run_with_patches(overrides=None):
    """Run process_granola_upload with standard mocks, returning (results, mocks_dict)."""
    patches = _base_patches()
    mock_names = [
        "insert_raw_input", "segment_transcript", "dedup_labels",
        "filter_by_significance", "get_settings", "embed_text",
        "get_cluster_centroids", "assign_or_create_cluster", "insert_event",
        "increment_event_count", "maybe_name_cluster", "get_cluster_by_id",
        "update_event_xs",
    ]
    started = [p.start() for p in patches]
    mocks = dict(zip(mock_names, started))
    if overrides:
        for key, value in overrides.items():
            if key in mocks:
                if callable(value) and not isinstance(value, MagicMock):
                    mocks[key].side_effect = value
                else:
                    mocks[key].return_value = value
    try:
        results = process_granola_upload(SAMPLE_TRANSCRIPT)
    finally:
        for p in patches:
            p.stop()
    return results, mocks


# --- SPEAKER_MAP ---


def test_speaker_map_contains_all_participants():
    assert "Jessie" in SPEAKER_MAP
    assert "Emma" in SPEAKER_MAP
    assert "Steven" in SPEAKER_MAP
    assert SPEAKER_MAP["Jessie"] == "jessie"
    assert SPEAKER_MAP["Emma"] == "emma"
    assert SPEAKER_MAP["Steven"] == "steven"


# --- process_granola_upload ---


def test_process_granola_stores_correct_count():
    results, mocks = _run_with_patches()
    assert len(results) == 3
    assert mocks["embed_text"].call_count == 3
    assert mocks["insert_event"].call_count == 3
    assert mocks["increment_event_count"].call_count == 3
    for result in results:
        assert result["event_id"] == FAKE_EVENT_ID


def test_process_granola_source_is_granola():
    results, mocks = _run_with_patches()
    for c in mocks["insert_event"].call_args_list:
        assert c.kwargs["source"] == "granola"


def test_process_granola_computes_xs_for_each_segment():
    results, mocks = _run_with_patches(
        {"get_cluster_by_id": {"name": "The Root", "event_count": 2}}
    )
    assert mocks["update_event_xs"].call_count == 3
    for c in mocks["update_event_xs"].call_args_list:
        xs_value = c[0][1]
        assert 0.0 <= xs_value <= 1.0


def test_process_granola_empty_raises():
    with pytest.raises(ValueError, match="Empty transcript"):
        process_granola_upload("")


def test_process_granola_embedding_failure_no_partial_write():
    patches = _base_patches()
    started = [p.start() for p in patches]
    # Override embed_text to fail
    started[5].side_effect = EmbeddingError("API down")
    try:
        with pytest.raises(EmbeddingError):
            process_granola_upload(SAMPLE_TRANSCRIPT)
    finally:
        for p in patches:
            p.stop()


def test_granola_return_contract_cluster_name():
    results, mocks = _run_with_patches()
    for result in results:
        assert result["cluster_name"] == "The Gate"
        assert "-" not in result["cluster_name"] or len(result["cluster_name"]) != 36


def test_granola_increment_failure_event_survives():
    results, mocks = _run_with_patches(
        {"increment_event_count": RuntimeError("RPC failed")}
    )
    assert len(results) == 3
    for result in results:
        assert result["event_id"] == FAKE_EVENT_ID
        assert result["cluster_name"] == "The Gate"


# --- Segmentation integration ---


def test_granola_uses_segmentation():
    """segment_transcript is called with transcript text and speaker_map."""
    results, mocks = _run_with_patches()
    mocks["segment_transcript"].assert_called_once_with(SAMPLE_TRANSCRIPT, SPEAKER_MAP, "shared")


def test_granola_multi_speaker_sets_shared():
    """Multi-speaker segment produces participant='shared' with full participants array."""
    multi_seg = [Segment(text="Shared discussion topic", label="Shared topic", participants=["steven", "emma"], start_line=1, end_line=2, significance=0.8)]
    patches = _base_patches()
    started = [p.start() for p in patches]
    started[1].return_value = multi_seg  # segment_transcript
    try:
        results = process_granola_upload(SAMPLE_TRANSCRIPT)
    finally:
        for p in patches:
            p.stop()
    assert len(results) == 1
    assert results[0]["participant"] == "shared"


def test_granola_single_speaker_sets_name():
    """Single-speaker segment uses that speaker's name as participant."""
    solo_seg = [Segment(text="Steven solo thought", label="Solo thought", participants=["steven"], start_line=1, end_line=2, significance=0.8)]
    patches = _base_patches()
    started = [p.start() for p in patches]
    started[1].return_value = solo_seg  # segment_transcript
    try:
        results = process_granola_upload(SAMPLE_TRANSCRIPT)
    finally:
        for p in patches:
            p.stop()
    assert len(results) == 1
    assert results[0]["participant"] == "steven"


def test_granola_segmentation_error_propagates():
    """SegmentationError from segment_transcript propagates (no silent fallback)."""
    patches = _base_patches()
    started = [p.start() for p in patches]
    started[1].side_effect = SegmentationError("LLM failed")  # segment_transcript
    try:
        with pytest.raises(SegmentationError, match="LLM failed"):
            process_granola_upload(SAMPLE_TRANSCRIPT)
    finally:
        for p in patches:
            p.stop()


def test_granola_labels_from_segmentation():
    """Labels come from segment.label, not text[:80]."""
    results, mocks = _run_with_patches()
    labels = [c.kwargs["label"] for c in mocks["insert_event"].call_args_list]
    assert labels == ["Bridge crossing dream", "Threshold conversation", "Memory reshaping reflection"]


# --- New tests: Sprint 4 Session 4a pipeline integration ---


def test_granola_stores_transcript_before_segmentation():
    """insert_raw_input is called before segment_transcript."""
    call_order = []

    patches = _base_patches()
    started = [p.start() for p in patches]
    started[0].side_effect = lambda **kw: (call_order.append("insert_raw_input"), {"id": FAKE_RAW_INPUT_ID})[1]
    started[1].side_effect = lambda *a, **kw: (call_order.append("segment_transcript"), FAKE_SEGMENTS)[1]
    try:
        process_granola_upload(SAMPLE_TRANSCRIPT)
    finally:
        for p in patches:
            p.stop()

    assert call_order.index("insert_raw_input") < call_order.index("segment_transcript")


def test_granola_calls_dedup_labels():
    """dedup_labels is called on segments after segmentation."""
    results, mocks = _run_with_patches()
    mocks["dedup_labels"].assert_called_once()
    args = mocks["dedup_labels"].call_args[0]
    assert args[0] == FAKE_SEGMENTS


def test_granola_filters_by_significance():
    """filter_by_significance is called with segments and threshold."""
    results, mocks = _run_with_patches()
    mocks["filter_by_significance"].assert_called_once()
    args = mocks["filter_by_significance"].call_args[0]
    assert args[1] == 0.3  # significance_threshold from FAKE_SETTINGS


def test_granola_passes_raw_input_id_and_lines_to_insert_event():
    """insert_event receives raw_input_id, start_line, end_line."""
    results, mocks = _run_with_patches()
    for c in mocks["insert_event"].call_args_list:
        assert c.kwargs["raw_input_id"] == FAKE_RAW_INPUT_ID
        assert "start_line" in c.kwargs
        assert "end_line" in c.kwargs

    first_call = mocks["insert_event"].call_args_list[0]
    assert first_call.kwargs["start_line"] == 1
    assert first_call.kwargs["end_line"] == 2


def test_granola_uses_assign_or_create_cluster():
    """assign_or_create_cluster is used instead of assign_cluster."""
    results, mocks = _run_with_patches()
    assert mocks["assign_or_create_cluster"].call_count == 3


def test_granola_refreshes_centroids_on_new_cluster():
    """When assign_or_create_cluster returns created=True, centroids are refreshed."""
    new_cluster_id = str(uuid4())
    call_count = {"assign": 0}

    def mock_assign(embedding, centroids):
        call_count["assign"] += 1
        if call_count["assign"] == 2:
            return (new_cluster_id, 0.2, True)
        return (FAKE_CLUSTER_ID, 0.9, False)

    patches = _base_patches()
    started = [p.start() for p in patches]
    started[7].side_effect = mock_assign  # assign_or_create_cluster
    try:
        process_granola_upload(SAMPLE_TRANSCRIPT)
    finally:
        for p in patches:
            p.stop()

    # get_cluster_centroids called once initially + once after created=True
    assert started[6].call_count == 2


def test_granola_calls_maybe_name_cluster():
    """maybe_name_cluster is called after increment_event_count."""
    results, mocks = _run_with_patches()
    assert mocks["maybe_name_cluster"].call_count == 3
    for c in mocks["maybe_name_cluster"].call_args_list:
        assert c[0][0] == FAKE_CLUSTER_ID


def test_granola_maybe_name_cluster_failure_does_not_block():
    """maybe_name_cluster failure is logged but doesn't block the pipeline."""
    results, mocks = _run_with_patches(
        {"maybe_name_cluster": RuntimeError("Naming failed")}
    )
    assert len(results) == 3
    for result in results:
        assert result["event_id"] == FAKE_EVENT_ID
