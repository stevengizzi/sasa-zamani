# Sprint 3.5, Fix Session F2: Boundary-Based Segmentation Prompt

## Context
This is a targeted fix session for a design flaw discovered during S3 (re-seed).

**Original session:** S1a (created `app/segmentation.py`)
**Issue type:** Category 3 — Scope Gap (small — changes internals of one module, public interface unchanged)
**Issue description:** The segmentation prompt asks Claude to return verbatim transcript text inside JSON segments. For large transcripts (80K-136K characters), this means Claude must generate ~25,000-30,000 output tokens — essentially retyping the entire document. This causes: (1) API calls that take 3-5+ minutes, (2) costs approaching the $0.50/transcript escalation threshold, (3) timeout and SDK reliability issues at high `max_tokens` values. The fix is to have Claude return **line-number boundaries** instead of verbatim text, then slice the original text in Python.
**Blocks sessions:** S3 (re-seed cannot complete without this fix)

## Pre-Flight Checks
Before making any changes:
1. Run the test suite:
   ```
   python -m pytest -n auto -q
   ```
   Expected: 162 passed, 3 skipped, 3 pre-existing errors
2. Verify git is clean: `git status`
3. Read the affected files to understand current state:
   - `app/segmentation.py` (full file — understand current prompt, parser, and helpers)
   - `tests/test_segmentation.py` (full file — understand what mock responses look like)

## Objective
Redesign the internals of `segment_transcript()` so that:
- The transcript is sent to Claude with **numbered lines**
- Claude returns **start/end line numbers** per segment (instead of verbatim text)
- Python slices the original text using those boundaries
- The public interface is **completely unchanged**: `segment_transcript()` still returns `list[Segment]` with `text`, `label`, and `participants` fields populated

This reduces Claude's output from ~25,000 tokens to ~500 tokens for a typical transcript, eliminating timeout, cost, and reliability issues.

## Requirements

### 1. Modify `SEGMENTATION_PROMPT` (the prompt template string)

Replace the current prompt that asks for verbatim text with one that:

a. **Instructs Claude that the transcript will be provided with line numbers** (e.g., `L001: Speaker A: Hello...`)

b. **Asks Claude to return a JSON array** where each segment has:
   ```json
   {
     "start_line": 1,
     "end_line": 14,
     "label": "Morning routine discussion",
     "speakers": ["Speaker A", "Speaker B"]
   }
   ```

c. **Includes the explicit JSON schema** in the prompt (same approach as current, just different fields)

d. **Instructs Claude:**
   - Segments must cover consecutive line ranges (no reordering)
   - `start_line` and `end_line` are inclusive (1-indexed)
   - Every content line should belong to exactly one segment (no gaps in coverage of non-empty lines, no overlaps)
   - Segments should be in order (each segment's `start_line` > previous segment's `end_line`)
   - Group consecutive speaker turns that share a theme into single segments
   - Labels should be 3-5 words
   - List all speakers who contributed to the segment

e. **Preserves the existing tone/quality instructions** for labels (the current prompt's guidance on label quality should carry over)

### 2. Modify `segment_transcript()` function body

a. **Pre-processing:** Before constructing the prompt, split the transcript into lines and create a numbered version:
   ```python
   lines = text.split('\n')
   numbered = '\n'.join(f'L{i+1:03d}: {line}' for i, line in enumerate(lines))
   ```
   Pass `numbered` (not raw `text`) to the prompt.

b. **Prompt construction:** Use the new `SEGMENTATION_PROMPT` with the numbered transcript and speaker_map context.

c. **Response parsing:** Parse Claude's JSON response. For each segment object:
   - Extract `start_line` and `end_line` (1-indexed, inclusive)
   - Slice from the **original `lines` array** (0-indexed, so `start_line - 1` through `end_line`)
   - Join the sliced lines with `'\n'` to reconstruct the segment text
   - Extract `label` and `speakers`, apply `_map_speakers()` as before
   - Build a `Segment(text=..., label=..., participants=...)`

d. **Validation on parsed response** — raise `SegmentationError` if:
   - Any segment is missing `start_line`, `end_line`, `label`, or `speakers`
   - `start_line > end_line`
   - `start_line < 1` or `end_line > len(lines)`
   - Segments overlap (a segment's `start_line <= previous segment's `end_line`)

e. **Strip empty text segments:** After slicing, if a segment's text is empty or whitespace-only after joining, skip it (do not include in output). This handles cases where Claude marks a range of blank lines as a segment boundary.

### 3. Reduce `max_tokens`

Change `max_tokens=32000` back to `max_tokens=4096`. With boundary-based output, Claude's response for even the largest transcript will be well under 1000 tokens. 4096 provides generous headroom.

### 4. Do NOT modify `generate_event_label()`

Leave it completely unchanged. It has its own prompt, its own `max_tokens`, and works correctly.

### 5. Do NOT modify `_create_client()`

Leave the `timeout=300.0` as-is. It's now more than sufficient for the reduced output volume, and provides a safety net.

### 6. Update `_map_speakers()` if needed

The `_map_speakers()` helper should still work — it takes a list of speaker strings and maps them. If the current implementation needs no changes to handle the new flow, leave it alone.

### 7. Update tests in `tests/test_segmentation.py`

The existing tests mock Claude's response with the **old format** (`text`, `label`, `speakers` in the JSON). These mocks need to be updated to use the **new format** (`start_line`, `end_line`, `label`, `speakers`).

**Tests to update** (update mock response format, keep the same assertions on the output `Segment` objects):
- `test_segment_transcript_returns_segments` — update mock to use line boundaries
- `test_segment_multi_speaker_attribution` — update mock
- `test_segment_single_speaker` — update mock
- `test_segment_unmapped_speaker_defaults` — update mock
- `test_segment_transcript_max_tokens` (from F1) — assert `max_tokens=4096` now

**Tests that should need NO changes** (they test error paths, not response format):
- `test_segment_api_failure_raises`
- `test_generate_event_label`
- `test_generate_event_label_api_failure`
- `test_segment_malformed_json_raises`

**New tests to add:**
- `test_segment_boundary_validation_start_gt_end` — mock response where `start_line > end_line`, verify `SegmentationError` raised
- `test_segment_boundary_validation_out_of_range` — mock response where `end_line` exceeds transcript line count, verify `SegmentationError` raised
- `test_segment_boundary_overlap_raises` — mock response with overlapping line ranges, verify `SegmentationError` raised
- `test_segment_text_sliced_from_original` — mock a boundary response, provide a known transcript, verify `Segment.text` contains the correct sliced lines (not text from the API response)

**Important test principle:** The input transcript used in tests must be multi-line so that line-number slicing is meaningful. Something like:
```python
SAMPLE_TRANSCRIPT = """Speaker A: Let's talk about the project
Speaker A: I think we should start with the backend
Speaker B: I agree, the API needs work
Speaker B: We should also consider the database
Speaker A: Good point about the database
Speaker B: Let's plan the frontend next"""
```

## Constraints
- Do NOT modify any files except `app/segmentation.py` and `tests/test_segmentation.py`
- Do NOT modify: any other `app/` files, any `scripts/` files, `static/index.html`, any other test files
- Do NOT change `generate_event_label()` in any way
- Do NOT change `_create_client()` in any way
- Do NOT change the `Segment` dataclass
- Do NOT change the `SegmentationError` class
- Do NOT change the `segment_transcript()` function signature
- The public contract is unchanged: callers still get `list[Segment]` with `.text`, `.label`, `.participants`
- Keep changes focused on prompt redesign and response parsing

## Affected Files
| File | Change |
|------|--------|
| `app/segmentation.py` | New `SEGMENTATION_PROMPT`, new parsing logic in `segment_transcript()`, `max_tokens` 32000→4096 |
| `tests/test_segmentation.py` | Update mock response format in ~5 existing tests, add 4 new boundary validation tests |

## Test Targets
After implementation:
- All existing tests pass (with updated mocks where needed)
- 4 new tests added
- Error-path tests unchanged
- `generate_event_label` tests unchanged
- Test command: `python -m pytest tests/test_segmentation.py -x -v` (scoped) then `python -m pytest -n auto -q` (full)

## Definition of Done
- [ ] `SEGMENTATION_PROMPT` asks for line boundaries, not verbatim text
- [ ] Transcript sent to Claude with numbered lines (`L001:` prefix)
- [ ] Response parser extracts `start_line`/`end_line` and slices original text
- [ ] Boundary validation raises `SegmentationError` on invalid ranges or overlaps
- [ ] `max_tokens=4096` in `segment_transcript()`
- [ ] `generate_event_label()` completely unchanged
- [ ] `_create_client()` completely unchanged (timeout stays 300.0)
- [ ] `Segment` dataclass unchanged
- [ ] `segment_transcript()` signature unchanged
- [ ] ~5 existing test mocks updated to new response format
- [ ] 4 new boundary validation tests added and passing
- [ ] All tests pass (full suite)
- [ ] No unrelated changes

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| Public interface unchanged | `segment_transcript` still returns `list[Segment]` with text, label, participants |
| Boundary parsing works | `test_segment_text_sliced_from_original` passes |
| Boundary validation works | 3 new validation tests pass |
| max_tokens reduced | `grep max_tokens app/segmentation.py` shows 4096 in segment_transcript |
| generate_event_label unchanged | `git diff app/segmentation.py` shows no changes to generate_event_label function |
| _create_client unchanged | `git diff app/segmentation.py` shows no changes to _create_client function |
| No unrelated files modified | `git diff --name-only` shows only the 2 affected files |
| All tests pass | Full suite passes |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include the structured JSON appendix.

**Write the close-out report to a file:**
docs/sprints/sprint-3.5/session-f2-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3.5/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3.5/session-f2-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (scoped): `python -m pytest tests/test_segmentation.py -x -v`
5. Files that should NOT have been modified: everything except `app/segmentation.py` and `tests/test_segmentation.py`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3.5/session-s3f2-review.md

## Session-Specific Review Focus (for @reviewer)
1. Verify the prompt asks for line boundaries, NOT verbatim text
2. Verify the numbered-line format is `L001:` style (1-indexed, zero-padded)
3. Verify text is sliced from the **original lines array**, not from the API response
4. Verify boundary validation catches: start > end, out of range, overlaps
5. Verify `max_tokens` is back to 4096
6. Verify `generate_event_label()` has zero changes (diff shows no modifications)
7. Verify `_create_client()` has zero changes
8. Verify `Segment` dataclass has zero changes
9. Verify `segment_transcript()` signature has zero changes
10. Verify updated test mocks use the new `{start_line, end_line, label, speakers}` format
11. Verify new boundary validation tests are non-trivial

## Sprint-Level Regression Checklist
- Pre-sprint: 147 passed, 3 skipped, 3 pre-existing errors
- Hard floor: ≥118 pass
- All critical invariants from review-context.md must hold

## Sprint-Level Escalation Criteria
1. Test pass count drops below 118
2. Any file outside the two affected files modified
3. Public interface of segment_transcript() changes in any way