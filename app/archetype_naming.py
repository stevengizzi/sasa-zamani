"""Deferred archetype naming — generates cluster names once enough events accumulate."""

import logging

import anthropic

from app.config import get_settings
from app.db import (
    get_cluster_by_id,
    get_cluster_events_labels,
    get_cluster_events_notes,
    update_cluster_name,
)

logger = logging.getLogger(__name__)


class ArchetypeNamingError(Exception):
    """Raised when the archetype naming API call fails."""


ARCHETYPE_NAMING_PROMPT = """\
You are naming a constellation of related events. Given the event labels and
their content below, propose an archetype name.

Rules:
- The name should follow the pattern "The [Noun]" or a short noun-phrase
- Write in the register of a scholar's margin note: precise, ancestral, not vague
- Never use: journey, transformation, growth, powerful, explore, reflect, \
synchronicity, discover, reveal, activation
- The name should feel found rather than made — as if it already existed and \
you are recognizing it
- Return ONLY the archetype name, nothing else

Event labels:
{labels}

Event content (excerpts):
{notes}
"""


def generate_archetype_name(event_labels: list[str], event_notes: list[str]) -> str:
    """Call Claude to generate an archetype name from event labels and notes.

    Returns the generated name string.
    Raises ArchetypeNamingError on API failure.
    """
    labels_block = "\n".join(f"- {label}" for label in event_labels)
    notes_block = "\n".join(f"- {note}" for note in event_notes)
    prompt = ARCHETYPE_NAMING_PROMPT.format(labels=labels_block, notes=notes_block)

    try:
        settings = get_settings()
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if not text:
            raise ArchetypeNamingError("Empty response from Claude")
        return text
    except ArchetypeNamingError:
        raise
    except Exception as exc:
        raise ArchetypeNamingError(f"Archetype naming failed: {exc}") from exc


def maybe_name_cluster(cluster_id: str) -> str | None:
    """Name a cluster if it has enough events and is still unnamed.

    Returns the new name, or None if naming was skipped or failed.
    """
    cluster = get_cluster_by_id(cluster_id)
    if cluster is None:
        return None

    if cluster["name"] != "The Unnamed":
        return None

    settings = get_settings()
    if cluster["event_count"] < settings.archetype_naming_threshold:
        return None

    labels = get_cluster_events_labels(cluster_id)
    notes = get_cluster_events_notes(cluster_id)

    try:
        name = generate_archetype_name(labels, notes)
    except ArchetypeNamingError:
        logger.error("Failed to generate archetype name for cluster %s", cluster_id)
        return None

    update_cluster_name(cluster_id, name)
    logger.info("Named cluster %s → %s", cluster_id, name)
    return name
