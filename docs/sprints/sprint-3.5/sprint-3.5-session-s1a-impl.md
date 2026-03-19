# Sprint 3.5, Session S1a: Thematic Segmentation Engine

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/myth.py` (reference for Claude API call pattern, model usage)
   - `app/granola.py` (understand current parsing to design replacement)
   - `docs/design-reference.md` (Copy Tone section — label quality should match project voice)
2. Run the test baseline:
   Full suite: `python -m pytest -n auto -q`
   Expected: 147 passed, 3 skipped, 3 pre-existing errors
3. Verify you are on the correct branch: `main`

## Objective
Create the thematic segmentation module (`app/segmentation.py`) that takes a raw transcript and returns semantically coherent segments with attributed speakers and LLM-generated labels via a single Claude API call.

## Requirements

1. **Create `app/segmentation.py`:**

   a. **`Segment` dataclass:**
   ```python
   @dataclass
   class Segment:
       text: str           # Full segment content
       label: str          # 3-5 word summary
       participants: list[str]  # Contributing speakers
   ```

   b. **`SegmentationError` exception class** for API failures and malformed responses.

   c. **`segment_transcript(text: str, speaker_map: dict[str, str], default_participant: str = "shared") -> list[Segment]`:**
   - Constructs a prompt asking Claude to segment the transcript into thematic units
   - The prompt must instruct Claude to:
     - Identify thematic boundaries where the conversation shifts topic
     - Group consecutive speaker turns that share a theme into single segments
     - For each segment, return: the full verbatim text, a 3-5 word label, and the list of speakers who contributed
     - Return JSON array format
   - Speaker names in the response should be mapped through `speaker_map` (e.g., "Speaker A" → "steven"). Unmapped speakers get `default_participant`.
   - Single Claude API call using `claude-sonnet-4-20250514` (consistent with `app/myth.py` pattern)
   - Parse Claude's JSON response into `list[Segment]`
   - On API failure: raise `SegmentationError` with descriptive message
   - On malformed JSON / missing fields: raise `SegmentationError` with descriptive message

   d. **`generate_event_label(text: str) -> str`:**
   - Standalone function for generating a 3-5 word label for a single message (used by Telegram pipeline)
   - Single small Claude API call using `claude-sonnet-4-20250514`
   - Returns the label string
   - On failure: raise `SegmentationError` (caller decides fallback behavior)

2. **Create `tests/test_segmentation.py`:**

   All Claude API calls must be mocked. Tests verify prompt construction, response parsing, and error handling — not live API behavior.

## Constraints
- Do NOT modify: any existing `app/` files, any existing `tests/` files, any `scripts/` files, `static/index.html`
- Do NOT add: new API endpoints, new dependencies (use `anthropic` SDK already in requirements)
- The Claude API call pattern should follow `app/myth.py`'s approach (direct Anthropic client usage)
- The segmentation prompt must request JSON output. Include explicit JSON schema in the prompt.

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write:
  1. `test_segment_transcript_returns_segments` — mock Claude response with 3 segments, verify list of Segment objects with correct fields
  2. `test_segment_multi_speaker_attribution` — mock response where one segment has 2+ speakers, verify all in participants list
  3. `test_segment_single_speaker` — mock response with single-speaker segment, verify participants has one entry
  4. `test_segment_unmapped_speaker_defaults` — mock response with unmapped speaker label, verify it resolves to default_participant
  5. `test_segment_api_failure_raises` — mock API error, verify SegmentationError raised
  6. `test_generate_event_label` — mock Claude response, verify label string returned
- Minimum new test count: 6
- Test command: `python -m pytest tests/test_segmentation.py -x -q`

## Definition of Done
- [ ] `app/segmentation.py` exists with `Segment`, `SegmentationError`, `segment_transcript()`, `generate_event_label()`
- [ ] Segmentation prompt requests JSON output with explicit schema
- [ ] Speaker mapping applied to Claude's response
- [ ] Error handling for API failure and malformed response
- [ ] All existing tests pass
- [ ] 6 new tests written and passing
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| No existing files modified | `git diff --name-only` shows only new files |
| All existing tests pass | Full suite: `python -m pytest -n auto -q` |
| Module is importable | `python -c "from app.segmentation import segment_transcript, generate_event_label"` |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-3.5/session-s1a-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3.5/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3.5/session-s1a-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (scoped): `python -m pytest tests/test_segmentation.py -x -q`
5. Files that should NOT have been modified: all existing `app/` files, all existing `tests/` files, all `scripts/` files, `static/index.html`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3.5/session-s1a-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the standard protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify the segmentation prompt requests structured JSON output with an explicit schema
2. Verify speaker mapping is applied AFTER Claude returns segments (Claude sees raw transcript, mapping happens in Python)
3. Verify `SegmentationError` is raised (not caught silently) on API failure and malformed response
4. Verify `generate_event_label` is a separate function with its own prompt (not a wrapper around `segment_transcript`)
5. Verify the Claude model used is `claude-sonnet-4-20250514`
6. Check that no existing files were modified

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Pre-sprint: 147 passed, 3 skipped, 3 pre-existing errors
- Hard floor: ≥118 pass

### Critical Invariants
- No existing app/ modules modified
- All existing tests pass unchanged
- No new API endpoints added

## Sprint-Level Escalation Criteria
1. Test pass count drops below 118
2. Segmentation prompt design reveals need for changes to existing modules → escalate
