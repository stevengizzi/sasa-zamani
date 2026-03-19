"""Granola transcript processor with thematic segmentation and speaker attribution."""

import logging

from app.clustering import assign_cluster, compute_xs
from app.db import (
    get_cluster_by_id,
    get_cluster_centroids,
    increment_event_count,
    insert_event,
    update_event_xs,
)
from app.embedding import EmbeddingError, embed_text
from app.segmentation import SegmentationError, segment_transcript

logger = logging.getLogger(__name__)

SPEAKER_MAP: dict[str, str] = {
    "Jessie": "jessie",
    "Emma": "emma",
    "Steven": "steven",
}


def process_granola_upload(
    transcript: str,
    speaker_map: dict[str, str] | None = None,
    default_participant: str = "shared",
) -> list[dict]:
    """Full pipeline: segment transcript → embed each segment → assign cluster → store events.

    Returns list of {"event_id": "...", "participant": "...", "cluster_name": "..."}.
    Raises ValueError on empty transcript.
    Raises SegmentationError on segmentation failure.
    Rolls back all events on any embedding failure (no partial uploads).
    """
    if not isinstance(transcript, str):
        raise TypeError(f"transcript must be a str, got {type(transcript).__name__}")

    if transcript.strip() == "":
        raise ValueError("Empty transcript")

    if speaker_map is None:
        speaker_map = SPEAKER_MAP

    segments = segment_transcript(transcript, speaker_map, default_participant)
    if len(segments) == 0:
        raise ValueError("Empty transcript")

    # Embed all segments first — fail fast before any DB writes
    embeddings = []
    for segment in segments:
        try:
            embedding = embed_text(segment.text)
        except EmbeddingError as exc:
            logger.error("Embedding failed for granola segment: %s", exc)
            raise
        embeddings.append(embedding)

    centroids = get_cluster_centroids()
    results = []

    for segment, embedding in zip(segments, embeddings):
        participant = (
            "shared"
            if len(segment.participants) != 1
            else segment.participants[0]
        )
        participants = segment.participants

        cluster_id, similarity = assign_cluster(embedding, centroids)
        logger.info(
            "Granola segment assigned to cluster %s (similarity=%.4f)",
            cluster_id,
            similarity,
        )

        row = insert_event(
            label=segment.label,
            note=segment.text,
            participant=participant,
            embedding=embedding,
            source="granola",
            cluster_id=cluster_id,
            participants=participants,
        )

        try:
            increment_event_count(cluster_id)
        except Exception as exc:
            logger.warning(
                "increment_event_count failed for cluster %s after event %s was inserted: %s",
                cluster_id, row.get("id"), exc,
            )

        cluster = get_cluster_by_id(cluster_id)
        try:
            if cluster is not None:
                event_count = cluster["event_count"]
                xs = compute_xs(cluster["name"], event_count - 1, event_count)
                update_event_xs(row["id"], xs)
        except Exception as exc:
            logger.warning("xs computation failed for event %s: %s", row.get("id"), exc)

        cluster_name = cluster["name"] if cluster is not None else cluster_id
        results.append({
            "event_id": row.get("id"),
            "participant": participant,
            "cluster_name": cluster_name,
        })

    return results
