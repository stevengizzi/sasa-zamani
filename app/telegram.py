"""Telegram webhook handler and message parsing."""

import logging
from collections import OrderedDict

from app.archetype_naming import maybe_name_cluster
from app.clustering import assign_or_create_cluster, compute_xs
from app.config import get_settings
from app.db import (
    get_cluster_by_id,
    get_cluster_centroids,
    increment_event_count,
    insert_event,
    insert_raw_input,
    update_event_xs,
)
from app.embedding import EmbeddingError, embed_text
from app.segmentation import SegmentationError, generate_event_label

logger = logging.getLogger(__name__)

PARTICIPANT_MAP: dict[str, str] = {
    # By Telegram username (without @)
    "emma_murf": "emma",
    # By full name (first_name + last_name from Telegram)
    "Jessie Lian": "jessie",
    "Steven Gizzi": "steven",
    "Emma Murphy": "emma",
    # By first_name alone (fallback)
    "Jessie": "jessie",
    "Steven": "steven",
    "Emma": "emma",
}

_DEDUP_CAP = 10_000
_processed_update_ids: OrderedDict[int, None] = OrderedDict()
_dedup_cap_warned: bool = False


def extract_message(update: dict) -> tuple[str, str, int] | None:
    """Parse a Telegram webhook update payload.

    Returns (text, participant_name, update_id) or None if not a text message.
    """
    if not isinstance(update, dict):
        raise TypeError(f"update must be a dict, got {type(update).__name__}")

    message = update.get("message")
    if message is None:
        logger.info("Update has no message field, skipping")
        return None

    update_id = update.get("update_id")
    if update_id is None:
        logger.warning("Update missing update_id")
        return None

    text = message.get("text")
    if text is None:
        logger.info("Non-text message received (update_id=%s), skipping", update_id)
        return None

    if text.strip() == "":
        logger.warning("Empty text message received (update_id=%s)", update_id)
        return None

    from_user = message.get("from", {})
    username = from_user.get("username", "")
    first_name = from_user.get("first_name", "")
    last_name = from_user.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()
    participant = (
        PARTICIPANT_MAP.get(username)
        or PARTICIPANT_MAP.get(full_name)
        or PARTICIPANT_MAP.get(first_name, "unknown")
    )

    return text, participant, update_id


def is_duplicate(update_id: int) -> bool:
    """Check if this update_id has already been processed. Uses capped in-memory set for v1."""
    global _dedup_cap_warned
    if not isinstance(update_id, int):
        raise TypeError(f"update_id must be an int, got {type(update_id).__name__}")

    if update_id in _processed_update_ids:
        return True

    if len(_processed_update_ids) >= _DEDUP_CAP:
        if not _dedup_cap_warned:
            logger.warning("Dedup set reached cap of %d; evicting oldest entries", _DEDUP_CAP)
            _dedup_cap_warned = True
        _processed_update_ids.popitem(last=False)

    _processed_update_ids[update_id] = None
    return False


def process_telegram_update(update: dict) -> dict:
    """Full pipeline: extract → dedup → label+sig → store raw → filter → embed → assign/create → insert → name.

    Returns a status dict with keys: processed, reason, event_id, raw_input_id.
    """
    extracted = extract_message(update)
    if extracted is None:
        return {"processed": False, "reason": "not_text_message", "event_id": None, "raw_input_id": None}

    text, participant, update_id = extracted

    if is_duplicate(update_id):
        return {"processed": False, "reason": "duplicate", "event_id": None, "raw_input_id": None}

    try:
        label, significance = generate_event_label(text)
    except (SegmentationError, Exception) as exc:
        logger.warning("Label generation failed: %s — falling back to text[:80]", exc)
        label = text[:80]
        significance = 1.0

    raw_input_id = None
    try:
        raw_row = insert_raw_input(
            text=text,
            source="telegram",
            source_metadata={"update_id": update_id, "participant": participant},
        )
        raw_input_id = raw_row["id"]
    except Exception as exc:
        logger.warning("insert_raw_input failed for update_id=%s: %s", update_id, exc)

    if significance < get_settings().significance_threshold:
        return {
            "processed": False,
            "reason": "below_significance",
            "event_id": None,
            "raw_input_id": raw_input_id,
        }

    try:
        embedding = embed_text(text)
    except EmbeddingError as exc:
        logger.error("Embedding failed for update_id=%s: %s", update_id, exc)
        return {"processed": False, "reason": "embedding_failed", "event_id": None, "raw_input_id": raw_input_id}

    try:
        centroids = get_cluster_centroids()
        cluster_id, similarity, created = assign_or_create_cluster(embedding, centroids)
        logger.info(
            "Assigned update_id=%s to cluster %s (similarity=%.4f, created=%s)",
            update_id,
            cluster_id,
            similarity,
            created,
        )
    except Exception as exc:
        logger.error("Cluster assignment failed for update_id=%s: %s", update_id, exc)
        return {"processed": False, "reason": "cluster_failed", "event_id": None, "raw_input_id": raw_input_id}

    try:
        row = insert_event(
            label=label,
            note=text,
            participant=participant,
            embedding=embedding,
            source="telegram",
            cluster_id=cluster_id,
            raw_input_id=raw_input_id,
        )
    except Exception as exc:
        logger.error("DB write failed for update_id=%s: %s", update_id, exc)
        return {"processed": False, "reason": "db_failed", "event_id": None, "raw_input_id": raw_input_id}

    try:
        increment_event_count(cluster_id)
    except Exception as exc:
        logger.warning(
            "increment_event_count failed for cluster %s after event %s was inserted: %s",
            cluster_id, row.get("id"), exc,
        )

    try:
        maybe_name_cluster(cluster_id)
    except Exception as exc:
        logger.warning("maybe_name_cluster failed for cluster %s: %s", cluster_id, exc)

    try:
        cluster = get_cluster_by_id(cluster_id)
        if cluster is not None:
            event_count = cluster["event_count"]
            xs = compute_xs(cluster["name"], event_count - 1, event_count)
            update_event_xs(row["id"], xs)
    except Exception as exc:
        logger.warning("xs computation failed for event %s: %s", row.get("id"), exc)

    return {"processed": True, "reason": "ok", "event_id": row.get("id"), "raw_input_id": raw_input_id}
