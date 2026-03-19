"""Thematic segmentation engine: segments transcripts and generates event labels via Claude."""

import json
from dataclasses import dataclass

import anthropic

from app.config import get_settings

MODEL = "claude-sonnet-4-20250514"

SEGMENTATION_PROMPT = """\
You are a transcript analyst. Segment the following transcript into thematic units.

Rules:
- Identify where the conversation shifts topic. Group consecutive speaker turns \
that share a theme into a single segment.
- For each segment, return the full verbatim text, a 3-5 word label, and the list \
of speakers who contributed.
- Return ONLY a JSON array matching this schema exactly:

```json
[
  {{
    "text": "Full verbatim segment text",
    "label": "3-5 word summary",
    "speakers": ["Speaker A", "Speaker B"]
  }}
]
```

Every segment must have all three fields. Do not wrap in markdown fences or add commentary.

Transcript:
{transcript}"""

LABEL_PROMPT = """\
Generate a 3-5 word label that captures the core theme of this message. \
Return ONLY the label text, nothing else.

Message:
{text}"""


class SegmentationError(Exception):
    """Raised on API failures or malformed responses during segmentation."""


@dataclass
class Segment:
    """A thematically coherent transcript segment."""

    text: str
    label: str
    participants: list[str]


def _create_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key)


def _map_speakers(
    raw_speakers: list[str],
    speaker_map: dict[str, str],
    default_participant: str,
) -> list[str]:
    return [speaker_map.get(speaker, default_participant) for speaker in raw_speakers]


def segment_transcript(
    text: str,
    speaker_map: dict[str, str],
    default_participant: str = "shared",
) -> list[Segment]:
    """Segment a transcript into thematic units via a single Claude API call.

    Args:
        text: Raw transcript text.
        speaker_map: Maps speaker labels in the transcript to participant names.
        default_participant: Fallback for unmapped speakers.

    Returns:
        List of Segment objects with mapped participant names.

    Raises:
        SegmentationError: On API failure or malformed response.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, got {type(text).__name__}")

    prompt = SEGMENTATION_PROMPT.format(transcript=text)

    try:
        client = _create_client()
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
    except Exception as exc:
        raise SegmentationError(f"Claude API call failed: {exc}") from exc

    try:
        segments_data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SegmentationError(f"Malformed JSON from Claude: {exc}") from exc

    if not isinstance(segments_data, list):
        raise SegmentationError(
            f"Expected JSON array, got {type(segments_data).__name__}"
        )

    segments: list[Segment] = []
    for i, item in enumerate(segments_data):
        if not isinstance(item, dict):
            raise SegmentationError(f"Segment {i} is not an object")
        missing = [f for f in ("text", "label", "speakers") if f not in item]
        if missing:
            raise SegmentationError(
                f"Segment {i} missing fields: {', '.join(missing)}"
            )
        participants = _map_speakers(item["speakers"], speaker_map, default_participant)
        segments.append(
            Segment(text=item["text"], label=item["label"], participants=participants)
        )

    return segments


def generate_event_label(text: str) -> str:
    """Generate a 3-5 word label for a single message via Claude.

    Args:
        text: The message text to label.

    Returns:
        A short label string.

    Raises:
        SegmentationError: On API failure.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, got {type(text).__name__}")

    prompt = LABEL_PROMPT.format(text=text)

    try:
        client = _create_client()
        response = client.messages.create(
            model=MODEL,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )
        label = response.content[0].text.strip()
    except Exception as exc:
        raise SegmentationError(f"Claude API call failed: {exc}") from exc

    if not label:
        raise SegmentationError("Claude returned empty label")

    return label
