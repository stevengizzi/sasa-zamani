"""Granola transcript parser with speaker attribution and segment extraction."""

import logging
import re

from app.clustering import assign_cluster
from app.db import get_cluster_centroids, increment_event_count, insert_event
from app.embedding import EmbeddingError, embed_text

logger = logging.getLogger(__name__)

SPEAKER_MAP: dict[str, str] = {
    "Jessie": "jessie",
    "Emma": "emma",
    "Steven": "steven",
}

_SPEAKER_PATTERN = re.compile(r"^([A-Z][a-zA-Z]+):\s*", re.MULTILINE)


def parse_transcript(transcript: str) -> list[dict]:
    """Parse a Granola-format transcript into attributed segments.

    Granola format: plain text with speaker labels like "Jessie: ...\\n\\nEmma: ..."
    Returns list of {"text": "...", "participant": "jessie"|"emma"|"steven"|"shared"}.
    """
    if not isinstance(transcript, str):
        raise TypeError(f"transcript must be a str, got {type(transcript).__name__}")

    stripped = transcript.strip()
    if stripped == "":
        return []

    splits = _SPEAKER_PATTERN.split(stripped)

    # If no speaker labels found, splits will have only one element (the full text)
    if len(splits) == 1:
        return [{"text": stripped, "participant": "shared"}]

    segments = []
    # splits[0] is text before the first speaker (usually empty)
    # Then pairs of (speaker_name, text) follow
    preamble = splits[0].strip()
    if preamble:
        segments.append({"text": preamble, "participant": "shared"})

    for i in range(1, len(splits), 2):
        speaker_name = splits[i]
        text = splits[i + 1].strip() if i + 1 < len(splits) else ""
        if text == "":
            continue
        participant = SPEAKER_MAP.get(speaker_name, speaker_name.lower())
        segments.append({"text": text, "participant": participant})

    return segments


def process_granola_upload(transcript: str) -> list[dict]:
    """Full pipeline: parse transcript → embed each segment → assign cluster → store events.

    Returns list of {"event_id": "...", "participant": "...", "cluster_name": "..."}.
    Raises ValueError on empty transcript.
    Rolls back all events on any embedding failure (no partial uploads).
    """
    if not isinstance(transcript, str):
        raise TypeError(f"transcript must be a str, got {type(transcript).__name__}")

    if transcript.strip() == "":
        raise ValueError("Empty transcript")

    segments = parse_transcript(transcript)
    if len(segments) == 0:
        raise ValueError("Empty transcript")

    # Embed all segments first — fail fast before any DB writes
    embeddings = []
    for segment in segments:
        try:
            embedding = embed_text(segment["text"])
        except EmbeddingError as exc:
            logger.error("Embedding failed for granola segment: %s", exc)
            raise
        embeddings.append(embedding)

    centroids = get_cluster_centroids()
    results = []

    for segment, embedding in zip(segments, embeddings):
        cluster_id, similarity = assign_cluster(embedding, centroids)
        logger.info(
            "Granola segment assigned to cluster %s (similarity=%.4f)",
            cluster_id,
            similarity,
        )

        label = segment["text"][:80] if len(segment["text"]) > 80 else segment["text"]
        row = insert_event(
            label=label,
            note=segment["text"],
            participant=segment["participant"],
            embedding=embedding,
            source="granola",
            cluster_id=cluster_id,
        )
        increment_event_count(cluster_id)

        # Look up cluster name for the response
        cluster_name = cluster_id
        results.append({
            "event_id": row.get("id"),
            "participant": segment["participant"],
            "cluster_name": cluster_name,
        })

    return results
