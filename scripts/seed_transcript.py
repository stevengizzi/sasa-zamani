"""Seed production database with Granola transcript data.

Uses thematic segmentation to split transcripts into semantically coherent
segments with LLM-generated labels, then runs each through the
embedding/clustering pipeline.

Usage examples:

    # March 17 — dry run
    python -m scripts.seed_transcript \\
      --file docs/source/3-17-granola-transcript.md \\
      --speaker-map '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}' \\
      --dry-run

    # March 17 — live
    python -m scripts.seed_transcript \\
      --file docs/source/3-17-granola-transcript.md \\
      --speaker-map '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}' \\
      --date 2025-03-17

    # March 18 — live
    python -m scripts.seed_transcript \\
      --file docs/source/3-18-granola-transcript.md \\
      --speaker-map '{"Speaker B": "emma", "Speaker C": "jessie", "Speaker F": "steven"}' \\
      --date 2025-03-18

    Note: March 18 unmapped speakers (A, D, E, G, H, I) default to "shared".
"""

import argparse
import json
import logging
import sys
from collections import Counter

from app.clustering import assign_cluster, compute_xs
from app.db import (
    get_cluster_by_id,
    get_cluster_centroids,
    increment_event_count,
    insert_event,
    update_event_xs,
)
from app.embedding import EmbeddingError, embed_text
from app.segmentation import Segment, segment_transcript

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed database from a Granola transcript using thematic segmentation."
    )
    parser.add_argument("--file", required=True, help="Path to transcript file")
    parser.add_argument(
        "--speaker-map",
        required=True,
        help=(
            "JSON mapping raw speaker labels in the transcript to participant names, "
            "e.g. '{\"Speaker A\": \"steven\"}'"
        ),
    )
    parser.add_argument(
        "--default-participant",
        default="shared",
        help="Participant name for unmapped speakers (default: shared)",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=100,
        help="Minimum segment character length (default: 100)",
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Event date in YYYY-MM-DD format (stored as event_date)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run segmentation and print analysis without DB/API calls",
    )
    return parser.parse_args(argv)


def filter_by_length(
    segments: list[Segment], min_length: int
) -> list[Segment]:
    """Return only segments whose text meets the minimum character length."""
    return [s for s in segments if len(s.text) >= min_length]


def _resolve_participant(segment: Segment) -> str:
    """Derive the single participant string from a segment's participants list."""
    if len(segment.participants) != 1:
        return "shared"
    return segment.participants[0]


def print_dry_run(
    all_segments: list[Segment],
    filtered_segments: list[Segment],
) -> None:
    """Print dry-run analysis to stdout."""
    participant_counts: Counter[str] = Counter(
        _resolve_participant(s) for s in filtered_segments
    )

    print(f"Total segments found (before filtering): {len(all_segments)}")
    print(f"Segments after filtering: {len(filtered_segments)}")
    print(f"Segment count per participant: {dict(participant_counts)}")
    print()
    for i, segment in enumerate(filtered_segments, 1):
        participant = _resolve_participant(segment)
        speakers = ", ".join(segment.participants)
        print(f"  [{i}] ({participant} | speakers: {speakers}) {segment.label}")
        preview = segment.text[:80]
        print(f"       {preview}")


def run_pipeline(segments: list[Segment], event_date: str | None = None) -> None:
    """Run each segment through embed → assign → insert → increment → xs pipeline."""
    total = len(segments)
    inserted = 0
    skipped = 0
    participant_counts: Counter[str] = Counter()
    cluster_counts: Counter[str] = Counter()

    centroids = get_cluster_centroids()

    for i, segment in enumerate(segments, 1):
        participant = _resolve_participant(segment)

        try:
            embedding = embed_text(segment.text)
        except EmbeddingError as exc:
            logger.error("Embedding failed for segment %d: %s", i, exc)
            skipped += 1
            continue

        try:
            cluster_id, similarity = assign_cluster(embedding, centroids)
            row = insert_event(
                label=segment.label,
                note=segment.text,
                participant=participant,
                embedding=embedding,
                source="granola",
                cluster_id=cluster_id,
                event_date=event_date,
                participants=segment.participants,
            )
        except Exception as exc:
            logger.error("DB insert failed for segment %d: %s", i, exc)
            skipped += 1
            continue

        try:
            increment_event_count(cluster_id)
        except Exception as exc:
            logger.warning(
                "increment_event_count failed for cluster %s: %s", cluster_id, exc
            )

        cluster = None
        try:
            cluster = get_cluster_by_id(cluster_id)
            if cluster is not None:
                event_count = cluster["event_count"]
                xs = compute_xs(cluster["name"], event_count - 1, event_count)
                update_event_xs(row["id"], xs)
        except Exception as exc:
            logger.warning("xs computation failed for event %s: %s", row.get("id"), exc)

        cluster_name = (
            cluster["name"] if cluster is not None else cluster_id
        )
        inserted += 1
        participant_counts[participant] += 1
        cluster_counts[cluster_name] += 1

        if i % 10 == 0:
            print(f"Processed {i}/{total} segments...")

    print(f"\nDone. Inserted: {inserted}, Skipped: {skipped}")
    print(f"Per-participant: {dict(participant_counts)}")
    print(f"Per-cluster: {dict(cluster_counts)}")


def main(argv: list[str] | None = None) -> None:
    """Entry point for seed_transcript script."""
    args = parse_args(argv)

    speaker_map = json.loads(args.speaker_map)
    if not isinstance(speaker_map, dict):
        print("Error: --speaker-map must be a JSON object", file=sys.stderr)
        sys.exit(1)

    with open(args.file) as f:
        transcript_text = f.read()

    all_segments = segment_transcript(
        transcript_text, speaker_map, args.default_participant
    )
    filtered_segments = filter_by_length(all_segments, args.min_length)

    if args.dry_run:
        print_dry_run(all_segments, filtered_segments)
        return

    logging.basicConfig(level=logging.INFO)
    run_pipeline(filtered_segments, event_date=args.date)


if __name__ == "__main__":
    main()
