"""One-off sanity check: embed test messages and verify cluster assignment against seed archetypes."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.clustering import SEED_ARCHETYPES, assign_cluster, compute_seed_centroids
from app.embedding import embed_texts

test_messages = [
    ("We cooked dinner together and shared stories around the table", "The Table"),
    ("I dreamt I was standing at a door that kept moving further away", "The Gate"),
    ("Went swimming at dawn, the water remembered my body before I did", "What the Body Keeps"),
    ("Sat alone for an hour. Said nothing. It was enough.", "The Silence"),
    ("My grandmother used to say that word differently", "The Root"),
    ("Spent the morning writing field notes about yesterday", "The Hand"),
]


def main() -> None:
    print("Computing seed centroids...")
    centroid_map = compute_seed_centroids()

    # Build centroids list as (name, embedding) for assign_cluster
    centroids = [(name, embedding) for name, embedding in centroid_map.items()]

    print("Embedding test messages...")
    texts = [msg for msg, _ in test_messages]
    embeddings = embed_texts(texts)

    matches = 0
    print()
    print(f"{'Message':<62} {'Expected':<22} {'Actual':<22} {'Score':>6}  {'Result'}")
    print("-" * 130)

    for (text, expected), embedding in zip(test_messages, embeddings):
        cluster_name, score = assign_cluster(embedding, centroids)
        matched = cluster_name == expected
        if matched:
            matches += 1
        flag = "MATCH" if matched else "MISMATCH"
        truncated = text[:60] if len(text) > 60 else text
        print(f"{truncated:<62} {expected:<22} {cluster_name:<22} {score:>6.4f}  {flag}")

    print()
    print(f"Summary: {matches}/{len(test_messages)} matched expected cluster")


if __name__ == "__main__":
    main()
