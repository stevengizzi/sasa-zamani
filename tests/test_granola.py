"""Tests for Granola transcript parser and pipeline."""

from unittest.mock import patch
from uuid import uuid4

import pytest

from app.embedding import EmbeddingError
from app.granola import SPEAKER_MAP, parse_transcript, process_granola_upload

SAMPLE_TRANSCRIPT = (
    "Jessie: I had the strangest dream last night about crossing a bridge"
    " that kept extending.\n\n"
    "Emma: That reminds me of the conversation we had about thresholds."
    " The food was incredible at that dinner, by the way.\n\n"
    "Steven: I've been writing about exactly this — the way memory reshapes"
    " when you try to pin it down."
)

FAKE_EMBEDDING = [0.1] * 1536
FAKE_CLUSTER_ID = str(uuid4())
FAKE_EVENT_ID = str(uuid4())


# --- parse_transcript ---


def test_parse_multi_speaker():
    segments = parse_transcript(SAMPLE_TRANSCRIPT)
    assert len(segments) == 3
    assert segments[0]["participant"] == "jessie"
    assert segments[1]["participant"] == "emma"
    assert segments[2]["participant"] == "steven"


def test_parse_single_speaker():
    transcript = "Jessie: Just one thing to say about today."
    segments = parse_transcript(transcript)
    assert len(segments) == 1
    assert segments[0]["participant"] == "jessie"
    assert "one thing" in segments[0]["text"]


def test_parse_no_speaker_labels():
    transcript = "A shared thought with no attribution at all."
    segments = parse_transcript(transcript)
    assert len(segments) == 1
    assert segments[0]["participant"] == "shared"
    assert segments[0]["text"] == transcript


def test_parse_empty_string():
    assert parse_transcript("") == []


def test_parse_whitespace_only():
    assert parse_transcript("   \n\n  ") == []


def test_parse_varied_spacing():
    transcript = "Jessie:   lots of spaces here\n\nEmma:tight text"
    segments = parse_transcript(transcript)
    assert len(segments) == 2
    assert segments[0]["participant"] == "jessie"
    assert segments[0]["text"] == "lots of spaces here"
    assert segments[1]["participant"] == "emma"
    assert segments[1]["text"] == "tight text"


def test_parse_unknown_speaker_lowercased():
    transcript = "Kai: Something from an unknown speaker."
    segments = parse_transcript(transcript)
    assert len(segments) == 1
    assert segments[0]["participant"] == "kai"


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
def test_process_granola_stores_correct_count(mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
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
def test_process_granola_source_is_granola(mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    process_granola_upload(SAMPLE_TRANSCRIPT)
    for call in mock_insert.call_args_list:
        assert call.kwargs["source"] == "granola"


@patch("app.granola.update_event_xs")
@patch("app.granola.get_cluster_by_id", return_value={"name": "The Root", "event_count": 2})
@patch("app.granola.increment_event_count")
@patch("app.granola.insert_event", return_value={"id": FAKE_EVENT_ID})
@patch("app.granola.get_cluster_centroids", return_value=[(FAKE_CLUSTER_ID, [0.1] * 1536)])
@patch("app.granola.embed_text", return_value=FAKE_EMBEDDING)
def test_process_granola_computes_xs_for_each_segment(mock_embed, mock_centroids, mock_insert, mock_incr, mock_cluster, mock_xs):
    results = process_granola_upload(SAMPLE_TRANSCRIPT)
    assert mock_xs.call_count == 3
    for call in mock_xs.call_args_list:
        xs_value = call[0][1]
        assert 0.0 <= xs_value <= 1.0


def test_process_granola_empty_raises():
    with pytest.raises(ValueError, match="Empty transcript"):
        process_granola_upload("")


@patch("app.granola.embed_text", side_effect=EmbeddingError("API down"))
def test_process_granola_embedding_failure_no_partial_write(mock_embed):
    with pytest.raises(EmbeddingError):
        process_granola_upload(SAMPLE_TRANSCRIPT)
