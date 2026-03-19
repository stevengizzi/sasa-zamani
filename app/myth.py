"""Claude API proxy for myth generation, prompt construction, and response caching."""

import anthropic

from app.config import get_settings
from app.db import (
    get_cluster_by_id,
    get_cluster_events_labels,
    get_latest_myth,
    insert_myth,
    update_cluster_myth,
)

PROHIBITED_WORDS = (
    "detect, discover, reveal, collective unconscious, synchronicity, "
    "universe, field, activate, activation, signal, journey, transformation, "
    "powerful, growth, explore, reflect, unlock"
)

PREFERRED_WORDS = (
    "scaffold, propose, candidate, resonate, vessel, compost, "
    "harvest window, rhyme, constellation, intersubjective, "
    "meaning-making, narrative commons"
)


def build_myth_prompt(cluster_name: str, event_labels: list[str]) -> str:
    """Construct a prompt for Claude in the ancestral register."""
    labels_block = "\n".join(f"- {label}" for label in event_labels)
    return (
        f"You are speaking in an ancestral register — not explanation, not analysis. "
        f"Short, poetic, oracular.\n\n"
        f"Archetype: {cluster_name}\n"
        f"Events in this cluster:\n{labels_block}\n\n"
        f"Write one sentence (20-35 words) in an ancestral register that names what "
        f"this cluster is actually about — what thread runs through all these moments. "
        f"Speak as if from the past looking forward. No quotation marks.\n\n"
        f"Do NOT use these words: {PROHIBITED_WORDS}\n\n"
        f"Prefer these words where they fit naturally: {PREFERRED_WORDS}"
    )


def should_regenerate(cluster_id: str, current_event_count: int) -> bool:
    """Return True if myth should be regenerated for this cluster."""
    latest = get_latest_myth(cluster_id)
    if latest is None:
        return True
    event_count_at_gen = latest.get("event_count_at_generation", 0)
    return current_event_count - event_count_at_gen >= 3


def generate_myth(cluster_id: str, cluster_name: str, event_labels: list[str]) -> str:
    """Call Claude to generate a mythic sentence. Returns fallback on error."""
    prompt = build_myth_prompt(cluster_name, event_labels)
    try:
        client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if not text:
            return "The pattern holds."
        return text
    except Exception:
        return "The pattern holds."


def get_or_generate_myth(cluster_id: str) -> tuple[str, bool]:
    """Fetch cached myth or generate a new one. Returns (myth_text, is_cached)."""
    cluster = get_cluster_by_id(cluster_id)
    if cluster is None:
        raise ValueError(f"Cluster not found: {cluster_id}")

    cluster_name = cluster["name"]
    event_count = cluster["event_count"]

    if not should_regenerate(cluster_id, event_count):
        cached = get_latest_myth(cluster_id)
        if cached is not None:
            return (cached["text"], True)

    event_labels = get_cluster_events_labels(cluster_id)
    new_text = generate_myth(cluster_id, cluster_name, event_labels)

    latest = get_latest_myth(cluster_id)
    new_version = (latest["version"] + 1) if latest is not None else 1

    insert_myth(cluster_id, new_text, event_count, new_version)
    update_cluster_myth(cluster_id, new_text)

    return (new_text, False)
