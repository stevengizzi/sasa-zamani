"""Backfill xs values for all events in the database.

Idempotent: overwrites existing xs values (deterministic jitter means
rerunning produces identical results).

Usage:
    python -m scripts.backfill_xs
    python scripts/backfill_xs.py
"""

import sys
from collections import defaultdict
from pathlib import Path

# Allow running as `python scripts/backfill_xs.py` from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.clustering import compute_xs
from app.db import get_db, update_event_xs


def main() -> None:
    db = get_db()

    clusters = db.table("clusters").select("id, name").execute().data
    cluster_name_by_id = {row["id"]: row["name"] for row in clusters}

    events = db.table("events").select("id, cluster_id").execute().data

    events_by_cluster: dict[str, list[str]] = defaultdict(list)
    for event in events:
        cluster_id = event.get("cluster_id")
        if cluster_id is not None:
            events_by_cluster[cluster_id].append(event["id"])

    updated = 0
    for cluster_id, event_ids in events_by_cluster.items():
        cluster_name = cluster_name_by_id.get(cluster_id, "unknown")
        cluster_event_count = len(event_ids)
        for event_index, event_id in enumerate(event_ids):
            xs = compute_xs(cluster_name, event_index, cluster_event_count)
            update_event_xs(event_id, xs)
            updated += 1

    print(f"Updated {updated} events with xs values")


if __name__ == "__main__":
    main()
