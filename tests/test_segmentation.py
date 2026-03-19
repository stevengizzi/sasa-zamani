"""Tests for thematic segmentation engine (app/segmentation.py)."""

import json
from unittest.mock import MagicMock, patch

import anthropic
import pytest

from app.segmentation import (
    Segment,
    SegmentationError,
    dedup_labels,
    filter_by_significance,
    generate_event_label,
    segment_transcript,
)

SPEAKER_MAP = {"Speaker A": "steven", "Speaker B": "jessie", "Speaker C": "emma"}

SAMPLE_TRANSCRIPT = """Speaker A: Let's talk about the project
Speaker A: I think we should start with the backend
Speaker B: I agree, the API needs work
Speaker B: We should also consider the database
Speaker A: Good point about the database
Speaker B: Let's plan the frontend next"""


def _mock_claude_response(text: str) -> MagicMock:
    """Build a mock Anthropic messages.create response."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


THREE_SEGMENTS = json.dumps([
    {
        "start_line": 1,
        "end_line": 2,
        "label": "Revisiting clustering strategy",
        "speakers": ["Speaker A"],
    },
    {
        "start_line": 3,
        "end_line": 4,
        "label": "Centroid drift observation",
        "speakers": ["Speaker B"],
    },
    {
        "start_line": 5,
        "end_line": 6,
        "label": "Planning review session",
        "speakers": ["Speaker C"],
    },
])


class TestSegmentTranscript:
    """Tests for segment_transcript()."""

    @patch("app.segmentation._create_client")
    def test_segment_transcript_returns_segments(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(THREE_SEGMENTS)
        mock_client_factory.return_value = mock_client

        result = segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

        assert len(result) == 3
        assert all(isinstance(s, Segment) for s in result)
        assert result[0].label == "Revisiting clustering strategy"
        assert result[0].participants == ["steven"]
        assert result[1].participants == ["jessie"]
        assert result[2].participants == ["emma"]

    @patch("app.segmentation._create_client")
    def test_segment_multi_speaker_attribution(self, mock_client_factory):
        multi_speaker = json.dumps([
            {
                "start_line": 1,
                "end_line": 6,
                "label": "Timeline discussion",
                "speakers": ["Speaker A", "Speaker B"],
            },
        ])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(multi_speaker)
        mock_client_factory.return_value = mock_client

        result = segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

        assert len(result) == 1
        assert result[0].participants == ["steven", "jessie"]

    @patch("app.segmentation._create_client")
    def test_segment_single_speaker(self, mock_client_factory):
        single = json.dumps([
            {
                "start_line": 1,
                "end_line": 6,
                "label": "Architecture musings",
                "speakers": ["Speaker A"],
            },
        ])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(single)
        mock_client_factory.return_value = mock_client

        result = segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

        assert len(result) == 1
        assert result[0].participants == ["steven"]

    @patch("app.segmentation._create_client")
    def test_segment_unmapped_speaker_defaults(self, mock_client_factory):
        unmapped = json.dumps([
            {
                "start_line": 1,
                "end_line": 6,
                "label": "Unknown contribution",
                "speakers": ["Speaker Z"],
            },
        ])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(unmapped)
        mock_client_factory.return_value = mock_client

        result = segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP, default_participant="shared")

        assert result[0].participants == ["shared"]

    @patch("app.segmentation._create_client")
    def test_segment_api_failure_raises(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.APIError(
            message="Service unavailable",
            request=MagicMock(),
            body=None,
        )
        mock_client_factory.return_value = mock_client

        with pytest.raises(SegmentationError, match="Claude API call failed"):
            segment_transcript("fake transcript", SPEAKER_MAP)

    @patch("app.segmentation._create_client")
    def test_segment_malformed_json_raises(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response("not json at all")
        mock_client_factory.return_value = mock_client

        with pytest.raises(SegmentationError, match="Malformed JSON"):
            segment_transcript("fake transcript", SPEAKER_MAP)

    @patch("app.segmentation._create_client")
    def test_segment_transcript_max_tokens(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(THREE_SEGMENTS)
        mock_client_factory.return_value = mock_client

        segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 4096

    @patch("app.segmentation._create_client")
    def test_segment_boundary_validation_start_gt_end(self, mock_client_factory):
        bad_range = json.dumps([
            {
                "start_line": 5,
                "end_line": 2,
                "label": "Bad range",
                "speakers": ["Speaker A"],
            },
        ])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(bad_range)
        mock_client_factory.return_value = mock_client

        with pytest.raises(SegmentationError, match="start_line 5 > end_line 2"):
            segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

    @patch("app.segmentation._create_client")
    def test_segment_boundary_validation_out_of_range(self, mock_client_factory):
        out_of_range = json.dumps([
            {
                "start_line": 1,
                "end_line": 100,
                "label": "Way too far",
                "speakers": ["Speaker A"],
            },
        ])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(out_of_range)
        mock_client_factory.return_value = mock_client

        with pytest.raises(SegmentationError, match="out of range"):
            segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

    @patch("app.segmentation._create_client")
    def test_segment_boundary_overlap_raises(self, mock_client_factory):
        overlapping = json.dumps([
            {
                "start_line": 1,
                "end_line": 4,
                "label": "First segment",
                "speakers": ["Speaker A"],
            },
            {
                "start_line": 3,
                "end_line": 6,
                "label": "Overlapping segment",
                "speakers": ["Speaker B"],
            },
        ])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(overlapping)
        mock_client_factory.return_value = mock_client

        with pytest.raises(SegmentationError, match="overlaps previous segment"):
            segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

    @patch("app.segmentation._create_client")
    def test_segment_text_sliced_from_original(self, mock_client_factory):
        boundaries = json.dumps([
            {
                "start_line": 1,
                "end_line": 2,
                "label": "Backend planning",
                "speakers": ["Speaker A"],
            },
            {
                "start_line": 3,
                "end_line": 6,
                "label": "Database and frontend",
                "speakers": ["Speaker A", "Speaker B"],
            },
        ])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(boundaries)
        mock_client_factory.return_value = mock_client

        result = segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

        assert result[0].text == (
            "Speaker A: Let's talk about the project\n"
            "Speaker A: I think we should start with the backend"
        )
        assert result[1].text == (
            "Speaker B: I agree, the API needs work\n"
            "Speaker B: We should also consider the database\n"
            "Speaker A: Good point about the database\n"
            "Speaker B: Let's plan the frontend next"
        )


class TestGenerateEventLabel:
    """Tests for generate_event_label()."""

    @patch("app.segmentation._create_client")
    def test_generate_event_label(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(
            json.dumps({"label": "Morning routine reflection", "significance": 0.7})
        )
        mock_client_factory.return_value = mock_client

        result = generate_event_label("I woke up early and journaled about my week.")

        assert result == ("Morning routine reflection", 0.7)
        mock_client.messages.create.assert_called_once()

    @patch("app.segmentation._create_client")
    def test_generate_event_label_returns_tuple(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(
            json.dumps({"label": "Quiet morning observation", "significance": 0.6})
        )
        mock_client_factory.return_value = mock_client

        result = generate_event_label("Watched the sunrise from my window.")

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "Quiet morning observation"
        assert result[1] == 0.6

    @patch("app.segmentation._create_client")
    def test_generate_event_label_defaults_significance(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(
            json.dumps({"label": "Solitary walk at dusk"})
        )
        mock_client_factory.return_value = mock_client

        label, significance = generate_event_label("Went for a walk as the sun set.")

        assert label == "Solitary walk at dusk"
        assert significance == 1.0

    @patch("app.segmentation._create_client")
    def test_generate_event_label_api_failure(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.APIError(
            message="Rate limit",
            request=MagicMock(),
            body=None,
        )
        mock_client_factory.return_value = mock_client

        with pytest.raises(SegmentationError, match="Claude API call failed"):
            generate_event_label("some text")


class TestSegmentDataclassFields:
    """Tests for Segment dataclass new fields."""

    def test_segment_has_start_line_end_line_significance(self):
        seg = Segment(text="hello", label="test", participants=["a"])
        assert seg.start_line == 0
        assert seg.end_line == 0
        assert seg.significance == 1.0

    def test_segment_fields_settable(self):
        seg = Segment(
            text="hello", label="test", participants=["a"],
            start_line=5, end_line=10, significance=0.7,
        )
        assert seg.start_line == 5
        assert seg.end_line == 10
        assert seg.significance == 0.7


THREE_SEGMENTS_WITH_SIGNIFICANCE = json.dumps([
    {
        "start_line": 1,
        "end_line": 2,
        "label": "Backend architecture debate",
        "speakers": ["Speaker A"],
        "significance": 0.9,
    },
    {
        "start_line": 3,
        "end_line": 4,
        "label": "Database schema concerns",
        "speakers": ["Speaker B"],
        "significance": 0.6,
    },
    {
        "start_line": 5,
        "end_line": 6,
        "label": "Scheduling the next session",
        "speakers": ["Speaker C"],
        "significance": 0.1,
    },
])

THREE_SEGMENTS_MISSING_SIGNIFICANCE = json.dumps([
    {
        "start_line": 1,
        "end_line": 2,
        "label": "Backend architecture debate",
        "speakers": ["Speaker A"],
    },
    {
        "start_line": 3,
        "end_line": 4,
        "label": "Database schema concerns",
        "speakers": ["Speaker B"],
        "significance": 0.6,
    },
    {
        "start_line": 5,
        "end_line": 6,
        "label": "Scheduling the next session",
        "speakers": ["Speaker C"],
    },
])


class TestSegmentTranscriptSignificance:
    """Tests for significance parsing in segment_transcript()."""

    @patch("app.segmentation._create_client")
    def test_parses_significance_from_response(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(
            THREE_SEGMENTS_WITH_SIGNIFICANCE
        )
        mock_client_factory.return_value = mock_client

        result = segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

        assert result[0].significance == 0.9
        assert result[1].significance == 0.6
        assert result[2].significance == 0.1

    @patch("app.segmentation._create_client")
    def test_defaults_significance_to_1_when_missing(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(
            THREE_SEGMENTS_MISSING_SIGNIFICANCE
        )
        mock_client_factory.return_value = mock_client

        result = segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

        assert result[0].significance == 1.0  # missing → default
        assert result[1].significance == 0.6  # present
        assert result[2].significance == 1.0  # missing → default

    @patch("app.segmentation._create_client")
    def test_clamps_out_of_range_significance(self, mock_client_factory):
        out_of_range = json.dumps([
            {
                "start_line": 1,
                "end_line": 3,
                "label": "Over the top",
                "speakers": ["Speaker A"],
                "significance": 1.5,
            },
            {
                "start_line": 4,
                "end_line": 6,
                "label": "Below zero",
                "speakers": ["Speaker B"],
                "significance": -0.3,
            },
        ])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(out_of_range)
        mock_client_factory.return_value = mock_client

        result = segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

        assert result[0].significance == 1.0  # clamped from 1.5
        assert result[1].significance == 0.0  # clamped from -0.3

    @patch("app.segmentation._create_client")
    def test_populates_start_line_end_line(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_claude_response(
            THREE_SEGMENTS_WITH_SIGNIFICANCE
        )
        mock_client_factory.return_value = mock_client

        result = segment_transcript(SAMPLE_TRANSCRIPT, SPEAKER_MAP)

        assert result[0].start_line == 1
        assert result[0].end_line == 2
        assert result[1].start_line == 3
        assert result[1].end_line == 4
        assert result[2].start_line == 5
        assert result[2].end_line == 6


class TestFilterBySignificance:
    """Tests for filter_by_significance()."""

    def _make_segment(self, label: str, significance: float) -> Segment:
        return Segment(
            text="text", label=label, participants=["a"],
            start_line=1, end_line=2, significance=significance,
        )

    def test_returns_segments_at_or_above_threshold(self):
        segs = [
            self._make_segment("high", 0.8),
            self._make_segment("exact", 0.3),
            self._make_segment("low", 0.1),
        ]
        result = filter_by_significance(segs, 0.3)
        assert len(result) == 2
        assert result[0].label == "high"
        assert result[1].label == "exact"

    def test_excludes_segments_below_threshold(self):
        segs = [
            self._make_segment("high", 0.9),
            self._make_segment("low", 0.2),
        ]
        result = filter_by_significance(segs, 0.3)
        assert len(result) == 1
        assert result[0].label == "high"

    def test_returns_empty_when_all_below(self):
        segs = [
            self._make_segment("a", 0.1),
            self._make_segment("b", 0.05),
        ]
        result = filter_by_significance(segs, 0.3)
        assert result == []

    def test_does_not_mutate_input(self):
        segs = [
            self._make_segment("high", 0.9),
            self._make_segment("low", 0.1),
        ]
        original_len = len(segs)
        filter_by_significance(segs, 0.3)
        assert len(segs) == original_len


class TestDedupLabels:
    """Tests for dedup_labels()."""

    def _make_segment(self, label: str) -> Segment:
        return Segment(
            text="text", label=label, participants=["a"],
            start_line=1, end_line=2, significance=0.5,
        )

    def test_unchanged_when_no_duplicates(self):
        segs = [self._make_segment("Alpha"), self._make_segment("Beta")]
        result = dedup_labels(segs)
        assert [s.label for s in result] == ["Alpha", "Beta"]

    def test_appends_ii_to_second_duplicate(self):
        segs = [self._make_segment("Same"), self._make_segment("Same")]
        result = dedup_labels(segs)
        assert result[0].label == "Same"
        assert result[1].label == "Same (II)"

    def test_appends_ii_iii_for_triple(self):
        segs = [self._make_segment("Same")] * 3
        result = dedup_labels(segs)
        assert result[0].label == "Same"
        assert result[1].label == "Same (II)"
        assert result[2].label == "Same (III)"

    def test_does_not_mutate_input(self):
        segs = [self._make_segment("Same"), self._make_segment("Same")]
        original_labels = [s.label for s in segs]
        dedup_labels(segs)
        assert [s.label for s in segs] == original_labels
