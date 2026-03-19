"""Thematic segmentation engine: segments transcripts and generates event labels via Claude."""

import json
import logging
from dataclasses import dataclass

import anthropic

from app.config import get_settings

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"

SEGMENTATION_PROMPT = """\
You are a transcript analyst. Segment the following transcript into thematic units.

The transcript below is provided with numbered lines (L001, L002, etc.).

Rules:
- Identify where the conversation shifts topic. Group consecutive speaker turns \
that share a theme into a single segment.
- For each segment, return the start and end line numbers (inclusive, 1-indexed), \
a label, the list of speakers who contributed, and a significance score.
- Segments must cover consecutive line ranges — no reordering.
- Every content line should belong to exactly one segment (no gaps in coverage \
of non-empty lines, no overlaps).
- Segments must be in order: each segment's start_line > previous segment's end_line.
- Label: A 4-8 word label in the register of a scholar's notebook margin note — \
precise, evocative, never a vague keyword extraction. Write it as a proposition or \
observation, not a tag cloud. Example: 'Nakedness as awareness of mortality' not \
'Garden Eden Fall Naked'. Example: 'Violence as the prerequisite for order' not \
'Violence centralization power discussion'.
- Each label must be unique. If two segments share a theme, differentiate the labels \
by their specific angle or emphasis.
- List all speakers who contributed to the segment.
- Rate the significance of each segment on a scale from 0.0 to 1.0, where 1.0 is \
a rich thematic discussion and 0.0 is pure logistics (introductions, audio setup, \
scheduling, goodbyes). Content that is primarily administrative or procedural should \
score below 0.3.
- Return ONLY a JSON array matching this schema exactly:

```json
[
  {{
    "start_line": 1,
    "end_line": 14,
    "label": "Nakedness as awareness of mortality",
    "speakers": ["Speaker A", "Speaker B"],
    "significance": 0.85
  }}
]
```

Every segment must have all five fields. Do not wrap in markdown fences or add commentary.

Transcript:
{transcript}"""

LABEL_PROMPT = """\
Generate a label and significance score for this message. \
The label should be 4-8 words in the register of a scholar's notebook margin note — \
precise, evocative, never a vague keyword extraction. Write it as a proposition or \
observation, not a tag cloud.

Rate significance 0.0–1.0 where 1.0 is rich thematic content and 0.0 is pure logistics.

Return ONLY a JSON object matching this schema exactly:
{{"label": "...", "significance": 0.8}}

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
    start_line: int = 0
    end_line: int = 0
    significance: float = 1.0


def _create_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key, timeout=120.0)


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

    lines = text.split("\n")
    numbered = "\n".join(f"L{i + 1:03d}: {line}" for i, line in enumerate(lines))
    prompt = SEGMENTATION_PROMPT.format(transcript=numbered)

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

    prev_end = 0
    segments: list[Segment] = []
    for i, item in enumerate(segments_data):
        if not isinstance(item, dict):
            raise SegmentationError(f"Segment {i} is not an object")
        missing = [
            f
            for f in ("start_line", "end_line", "label", "speakers")
            if f not in item
        ]
        if missing:
            raise SegmentationError(
                f"Segment {i} missing fields: {', '.join(missing)}"
            )

        start = item["start_line"]
        end = item["end_line"]

        if start > end:
            raise SegmentationError(
                f"Segment {i} has start_line {start} > end_line {end}"
            )
        if start < 1 or end > len(lines):
            raise SegmentationError(
                f"Segment {i} out of range: lines {start}-{end} "
                f"(transcript has {len(lines)} lines)"
            )
        if start <= prev_end:
            raise SegmentationError(
                f"Segment {i} overlaps previous segment "
                f"(start_line {start} <= previous end_line {prev_end})"
            )

        segment_text = "\n".join(lines[start - 1 : end])
        prev_end = end

        if not segment_text.strip():
            continue

        raw_significance = item.get("significance")
        if raw_significance is None:
            logger.warning("Segment %d missing significance, defaulting to 1.0", i)
            significance = 1.0
        else:
            try:
                significance = float(raw_significance)
            except (TypeError, ValueError):
                logger.warning("Segment %d has non-numeric significance %r, defaulting to 1.0", i, raw_significance)
                significance = 1.0
            if significance < 0.0:
                logger.warning("Segment %d significance %f below 0.0, clamping to 0.0", i, significance)
                significance = 0.0
            elif significance > 1.0:
                logger.warning("Segment %d significance %f above 1.0, clamping to 1.0", i, significance)
                significance = 1.0

        participants = _map_speakers(item["speakers"], speaker_map, default_participant)
        segments.append(
            Segment(
                text=segment_text,
                label=item["label"],
                participants=participants,
                start_line=start,
                end_line=end,
                significance=significance,
            )
        )

    return segments


def filter_by_significance(segments: list[Segment], threshold: float) -> list[Segment]:
    """Return segments with significance >= threshold. Does not mutate input."""
    return [s for s in segments if s.significance >= threshold]


def dedup_labels(segments: list[Segment]) -> list[Segment]:
    """Deduplicate labels by appending ordinal suffixes. Does not mutate input.

    If "Network state identity formation" appears 3 times, the second becomes
    "Network state identity formation (II)" and the third "(III)".
    The first occurrence is unchanged.
    """
    _ordinals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    seen: dict[str, int] = {}
    result: list[Segment] = []
    for s in segments:
        count = seen.get(s.label, 0)
        seen[s.label] = count + 1
        if count == 0:
            result.append(Segment(
                text=s.text,
                label=s.label,
                participants=list(s.participants),
                start_line=s.start_line,
                end_line=s.end_line,
                significance=s.significance,
            ))
        else:
            suffix = _ordinals[count] if count < len(_ordinals) else str(count + 1)
            result.append(Segment(
                text=s.text,
                label=f"{s.label} ({suffix})",
                participants=list(s.participants),
                start_line=s.start_line,
                end_line=s.end_line,
                significance=s.significance,
            ))
    return result


def generate_event_label(text: str) -> tuple[str, float]:
    """Generate a label and significance score for a single message via Claude.

    Args:
        text: The message text to label.

    Returns:
        A tuple of (label, significance).

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
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
    except Exception as exc:
        raise SegmentationError(f"Claude API call failed: {exc}") from exc

    try:
        data = json.loads(raw)
        label = data["label"]
    except (json.JSONDecodeError, KeyError, TypeError):
        raise SegmentationError(f"Malformed label response from Claude: {raw}")

    if not label:
        raise SegmentationError("Claude returned empty label")

    significance = data.get("significance")
    if significance is None:
        logger.warning("Label response missing significance, defaulting to 1.0")
        significance = 1.0
    else:
        try:
            significance = float(significance)
        except (TypeError, ValueError):
            significance = 1.0

    return (label, significance)
