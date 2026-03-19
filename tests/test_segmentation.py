"""Tests for thematic segmentation engine (app/segmentation.py)."""

import json
from unittest.mock import MagicMock, patch

import anthropic
import pytest

from app.segmentation import (
    Segment,
    SegmentationError,
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
        mock_client.messages.create.return_value = _mock_claude_response("Morning routine reflection")
        mock_client_factory.return_value = mock_client

        label = generate_event_label("I woke up early and journaled about my week.")

        assert label == "Morning routine reflection"
        mock_client.messages.create.assert_called_once()

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
