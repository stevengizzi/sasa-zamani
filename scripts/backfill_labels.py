"""Backfill LLM-generated labels for existing Telegram events.

One-time utility. Fetches all events where source='telegram', generates a
3-5 word label via Claude, and updates the label field in Supabase.

Usage:
    python -m scripts.backfill_labels
"""

import logging
import sys

from dotenv import load_dotenv

from app.db import get_db
from app.segmentation import SegmentationError, generate_event_label

logger = logging.getLogger(__name__)


def backfill_telegram_labels() -> None:
    """Fetch telegram events, generate labels, and update each row."""
    db = get_db()
    response = db.table("events").select("id, label, note").eq("source", "telegram").execute()
    events = response.data

    if not events:
        print("No telegram events found.")
        return

    print(f"Found {len(events)} telegram events to backfill.\n")

    updated = 0
    skipped = 0

    for event in events:
        event_id = event["id"]
        old_label = event["label"]
        note = event["note"]

        try:
            new_label = generate_event_label(note)
        except (SegmentationError, TypeError) as exc:
            logger.warning("Label generation failed for event %s: %s", event_id, exc)
            skipped += 1
            continue

        db.table("events").update({"label": new_label}).eq("id", event_id).execute()
        updated += 1
        print(f"  [{updated}] {event_id}: '{old_label}' -> '{new_label}'")

    print(f"\nDone. Updated: {updated}, Skipped: {skipped}")


def main() -> None:
    """Entry point for backfill_labels script."""
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    backfill_telegram_labels()


if __name__ == "__main__":
    main()
