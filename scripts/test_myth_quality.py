"""Manual myth quality testing: generate myths for all populated clusters and print for review."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.db import get_supabase
from app.myth import generate_myth


def main() -> None:
    client = get_supabase()

    clusters_resp = (
        client.table("clusters")
        .select("id, name, event_count")
        .gt("event_count", 0)
        .execute()
    )
    clusters = clusters_resp.data
    if not clusters:
        print("No clusters with events found.")
        return

    total = len(clusters)
    generated = 0
    errors: list[str] = []

    for cluster in clusters:
        cluster_id = cluster["id"]
        cluster_name = cluster["name"]
        event_count = cluster["event_count"]

        events_resp = (
            client.table("events")
            .select("label")
            .eq("cluster_id", cluster_id)
            .execute()
        )
        labels = [e["label"] for e in events_resp.data if e.get("label")]

        print(f'=== {cluster_name} ({event_count} events) ===')
        truncated = [
            f'"{lbl[:60]}..."' if len(lbl) > 60 else f'"{lbl}"'
            for lbl in labels[:10]
        ]
        print(f"Events: {', '.join(truncated)}")
        if len(labels) > 10:
            print(f"  ... and {len(labels) - 10} more")

        try:
            myth = generate_myth(cluster_id, cluster_name, labels)
            print(f'Myth: "{myth}"')
            generated += 1
        except Exception as exc:
            print(f"ERROR: {exc}")
            errors.append(f"{cluster_name}: {exc}")

        print("---")

    print(f"\nSummary: {total} clusters, {generated} myths generated, {len(errors)} errors")
    if errors:
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
