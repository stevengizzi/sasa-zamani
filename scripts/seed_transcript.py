"""Seed production database with Granola transcript data.

Parses Speaker-labeled transcripts, remaps speakers to participants,
filters short segments, and runs each through the embedding/clustering pipeline.

Usage examples:

    # March 17 — dry run
    python -m scripts.seed_transcript \\
      --file docs/source/3-17-granola-transcript.md \\
      --speaker-map '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}' \\
      --dry-run

    # March 17 — live
    python -m scripts.seed_transcript \\
      --file docs/source/3-17-granola-transcript.md \\
      --speaker-map '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}'

    # March 18 — live
    python -m scripts.seed_transcript \\
      --file docs/source/3-18-granola-transcript.md \\
      --speaker-map '{"Speaker B": "emma", "Speaker C": "jessie", "Speaker F": "steven"}'

    Note: March 18 unmapped speakers (A, D, E, G, H, I) default to "shared".
"""

import argparse
import json
import logging
import re
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

logger = logging.getLogger(__name__)

_SPEAKER_PATTERN = re.compile(r"^(Speaker [A-Z]):\s*", re.MULTILINE)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed database from a Granola transcript."
    )
    parser.add_argument("--file", required=True, help="Path to transcript file")
    parser.add_argument(
        "--speaker-map",
        required=True,
        help='JSON mapping Speaker labels to participants, e.g. \'{"Speaker A": "steven"}\'',
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
        "--dry-run",
        action="store_true",
        help="Print analysis without DB/API calls",
    )
    return parser.parse_args(argv)


def parse_transcript(
    text: str,
    speaker_map: dict[str, str],
    default_participant: str,
) -> list[dict[str, str]]:
    """Parse a Speaker-labeled transcript into attributed segments.

    Returns list of {"text": "...", "participant": "..."}.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, got {type(text).__name__}")

    stripped = text.strip()
    if stripped == "":
        return []

    splits = _SPEAKER_PATTERN.split(stripped)

    segments: list[dict[str, str]] = []

    preamble = splits[0].strip()
    if preamble:
        segments.append({"text": preamble, "participant": default_participant})

    for i in range(1, len(splits), 2):
        speaker_label = splits[i]
        segment_text = splits[i + 1].strip() if i + 1 < len(splits) else ""
        if segment_text == "":
            continue
        participant = speaker_map.get(speaker_label, default_participant)
        segments.append({"text": segment_text, "participant": participant})

    return segments


def filter_by_length(
    segments: list[dict[str, str]], min_length: int
) -> list[dict[str, str]]:
    """Return only segments whose text meets the minimum character length."""
    return [s for s in segments if len(s["text"]) >= min_length]


def print_dry_run(
    all_segments: list[dict[str, str]],
    filtered_segments: list[dict[str, str]],
) -> None:
    """Print dry-run analysis to stdout."""
    participant_counts: Counter[str] = Counter(
        s["participant"] for s in filtered_segments
    )

    print(f"Total segments found (before filtering): {len(all_segments)}")
    print(f"Segments after filtering: {len(filtered_segments)}")
    print(f"Segment count per participant: {dict(participant_counts)}")
    print()
    for i, segment in enumerate(filtered_segments, 1):
        preview = segment["text"][:80]
        print(f"  [{i}] ({segment['participant']}) {preview}")


def run_pipeline(segments: list[dict[str, str]]) -> None:
    """Run each segment through embed → assign → insert → increment → xs pipeline."""
    total = len(segments)
    inserted = 0
    skipped = 0
    participant_counts: Counter[str] = Counter()
    cluster_counts: Counter[str] = Counter()

    centroids = get_cluster_centroids()

    for i, segment in enumerate(segments, 1):
        text = segment["text"]
        participant = segment["participant"]

        try:
            embedding = embed_text(text)
        except EmbeddingError as exc:
            logger.error("Embedding failed for segment %d: %s", i, exc)
            skipped += 1
            continue

        try:
            cluster_id, similarity = assign_cluster(embedding, centroids)
            label = text[:80]
            row = insert_event(
                label=label,
                note=text,
                participant=participant,
                embedding=embedding,
                source="granola",
                cluster_id=cluster_id,
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

    all_segments = parse_transcript(
        transcript_text, speaker_map, args.default_participant
    )
    filtered_segments = filter_by_length(all_segments, args.min_length)

    if args.dry_run:
        print_dry_run(all_segments, filtered_segments)
        return

    logging.basicConfig(level=logging.INFO)
    run_pipeline(filtered_segments)


if __name__ == "__main__":
    main()
