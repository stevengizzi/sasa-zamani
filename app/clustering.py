"""Cluster assignment, centroid management, and seed cluster definitions."""

import hashlib
import logging
import math

from app.config import get_settings
from app.embedding import embed_texts

logger = logging.getLogger(__name__)

SEED_ARCHETYPES = [
    {
        "name": "The Gate",
        "glyph_id": "gate",
        "tags": ["dream", "threshold", "migration"],
        "representative_text": (
            "A dream about crossing a threshold. The door that appears when you are"
            " ready to leave. Migration, departure, the moment before."
        ),
    },
    {
        "name": "What the Body Keeps",
        "glyph_id": "body",
        "tags": ["body", "water", "morning"],
        "representative_text": (
            "The body remembering what the mind forgot. Swimming before sunrise."
            " The tide-like return of physical knowledge."
        ),
    },
    {
        "name": "The Table",
        "glyph_id": "table",
        "tags": ["food", "connection", "social"],
        "representative_text": (
            "Dinner with everyone. The communal center. Being fed and feeding."
            " Gathering around what sustains."
        ),
    },
    {
        "name": "The Silence",
        "glyph_id": "silence",
        "tags": ["silence", "solitude"],
        "representative_text": (
            "The quiet that arrives when you stop speaking. Solitude as presence,"
            " not absence. The mark that holds space."
        ),
    },
    {
        "name": "The Root",
        "glyph_id": "root",
        "tags": ["memory", "family", "language"],
        "representative_text": (
            "Your grandmother's kitchen. The word for tooth in a language you"
            " half-remember. What the family line carries forward."
        ),
    },
    {
        "name": "The Hand",
        "glyph_id": "hand",
        "tags": ["writing", "fieldwork"],
        "representative_text": (
            "The act of writing it down. Fieldwork. Making a mark that outlasts"
            " the moment. The trace of attention."
        ),
    },
]


XS_CENTERS: dict[str, float] = {
    "The Gate": 0.12,
    "The Silence": 0.15,
    "The Hand": 0.25,
    "The Root": 0.38,
    "What the Body Keeps": 0.50,
    "The Table": 0.82,
}

_XS_SPREAD = 0.06
_DEFAULT_XS_CENTER = 0.50


def compute_xs(cluster_name: str, event_index: int, cluster_event_count: int) -> float:
    """Compute the semantic x-position for an event within its cluster.

    Maps cluster name to a canonical center on the inward-social spectrum,
    then applies a per-event offset with deterministic jitter so events
    within the same cluster spread out rather than stacking.
    """
    if not isinstance(cluster_name, str):
        raise TypeError(f"cluster_name must be a str, got {type(cluster_name).__name__}")
    if not isinstance(event_index, int) or not isinstance(cluster_event_count, int):
        raise TypeError("event_index and cluster_event_count must be ints")

    center = XS_CENTERS.get(cluster_name, _DEFAULT_XS_CENTER)

    if cluster_event_count <= 1:
        offset = 0.0
    else:
        offset = _XS_SPREAD * (2 * event_index / (cluster_event_count - 1) - 1)

    jitter_input = f"{cluster_name}:{event_index}".encode()
    jitter_hash = int(hashlib.sha256(jitter_input).hexdigest()[:8], 16)
    jitter = (jitter_hash / 0xFFFFFFFF - 0.5) * 0.01

    result = center + offset + jitter
    return max(0.0, min(1.0, result))


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors. Returns value between -1 and 1."""
    if not isinstance(vec_a, list) or not isinstance(vec_b, list):
        raise TypeError("Both arguments must be lists of floats")
    if len(vec_a) != len(vec_b):
        raise ValueError(f"Vectors must have equal length, got {len(vec_a)} and {len(vec_b)}")
    if len(vec_a) == 0:
        raise ValueError("Vectors must not be empty")

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        raise ValueError("Cannot compute cosine similarity for zero vectors")

    return dot_product / (magnitude_a * magnitude_b)


def assign_cluster(
    embedding: list[float],
    centroids: list[tuple[str, list[float]]],
) -> tuple[str, float]:
    """Assign an embedding to the nearest cluster by cosine similarity.

    Returns (best_cluster_id, similarity_score). Logs a warning if the best
    similarity is below the configured cluster_join_threshold.
    """
    if not isinstance(centroids, list) or len(centroids) == 0:
        raise ValueError("centroids must be a non-empty list of (id, embedding) tuples")

    best_id = centroids[0][0]
    best_score = cosine_similarity(embedding, centroids[0][1])

    for cluster_id, centroid in centroids[1:]:
        score = cosine_similarity(embedding, centroid)
        if score > best_score:
            best_id = cluster_id
            best_score = score

    settings = get_settings()
    if best_score < settings.cluster_join_threshold:
        logger.warning(
            "Best cluster similarity %.4f is below threshold %.4f for cluster %s",
            best_score,
            settings.cluster_join_threshold,
            best_id,
        )

    return best_id, best_score


def compute_seed_centroids() -> dict[str, list[float]]:
    """Embed each seed archetype's representative text and return {name: embedding}."""
    texts = [archetype["representative_text"] for archetype in SEED_ARCHETYPES]
    embeddings = embed_texts(texts)
    return {
        archetype["name"]: embedding
        for archetype, embedding in zip(SEED_ARCHETYPES, embeddings)
    }


def seed_clusters() -> None:
    """Insert the six seed clusters into the database. Idempotent — skips existing clusters."""
    from app.db import cluster_exists, insert_cluster

    centroids = compute_seed_centroids()

    for archetype in SEED_ARCHETYPES:
        name = archetype["name"]
        if cluster_exists(name):
            logger.info("Cluster %r already exists, skipping", name)
            continue
        insert_cluster(name=name, centroid_embedding=centroids[name], is_seed=True)
        logger.info("Inserted seed cluster %r", name)
