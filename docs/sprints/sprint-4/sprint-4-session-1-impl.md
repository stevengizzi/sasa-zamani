# Sprint 4, Session 1: Segmentation Core — Prompts, Dataclass, Significance, Labels, Dedup

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/segmentation.py`
   - `app/config.py`
   - `docs/design-reference.md` (Copy Tone section — label register target)
   - `docs/sprints/sprint-4/sprint-spec.md`
2. Run the test baseline:
   Full suite: `python -m pytest tests/ -x -q`
   Expected: 166 tests, all passing
3. Verify you are on the correct branch: `sprint-4`
4. Create branch if needed: `git checkout -b sprint-4`

## Objective
Redesign the segmentation and label prompts for data quality (significance scores, marginalia-register labels, uniqueness). Extend the Segment dataclass to carry start_line, end_line, and significance. Add utility functions for significance filtering and label deduplication.

## Requirements

1. In `app/config.py`, add to the Settings class:
   - `significance_threshold: float = 0.3`

2. In `app/segmentation.py`, redesign `SEGMENTATION_PROMPT`:
   - Add `significance` (float 0.0–1.0) to the per-segment JSON schema. Instruct: "Rate the significance of each segment on a scale from 0.0 to 1.0, where 1.0 is a rich thematic discussion and 0.0 is pure logistics (introductions, audio setup, scheduling, goodbyes). Content that is primarily administrative or procedural should score below 0.3."
   - Change the label instruction from "3-5 word label" to: "A 4-8 word label in the register of a scholar's notebook margin note — precise, evocative, never a vague keyword extraction. Write it as a proposition or observation, not a tag cloud. Example: 'Nakedness as awareness of mortality' not 'Garden Eden Fall Naked'. Example: 'Violence as the prerequisite for order' not 'Violence centralization power discussion'."
   - Add uniqueness instruction: "Each label must be unique. If two segments share a theme, differentiate the labels by their specific angle or emphasis."
   - Update the JSON schema example to include the significance field.

3. In `app/segmentation.py`, extend the `Segment` dataclass:
   - Add fields: `start_line: int`, `end_line: int`, `significance: float`

4. In `app/segmentation.py`, update `segment_transcript()`:
   - Parse `significance` from each segment in the Claude response. If missing, default to 1.0 and log a warning.
   - Populate `start_line` and `end_line` on each Segment from the response (these are already parsed but not stored on the dataclass — now they should be).
   - Validation: significance must be a number between 0.0 and 1.0 inclusive. If outside range, clamp and log a warning.

5. In `app/segmentation.py`, add a new function:
   ```python
   def filter_by_significance(segments: list[Segment], threshold: float) -> list[Segment]:
       """Return segments with significance >= threshold. Does not mutate input."""
   ```

6. In `app/segmentation.py`, add a new function:
   ```python
   def dedup_labels(segments: list[Segment]) -> list[Segment]:
       """Deduplicate labels by appending ordinal suffixes. Does not mutate input.
       
       If "Network state identity formation" appears 3 times, the second becomes
       "Network state identity formation (II)" and the third "(III)".
       The first occurrence is unchanged.
       """
   ```

7. In `app/segmentation.py`, redesign `LABEL_PROMPT`:
   - Change to return JSON: `{"label": "...", "significance": 0.8}`
   - Use the same marginalia register instruction as the segmentation prompt.
   - Add significance instruction: "Rate significance 0.0–1.0 where 1.0 is rich thematic content and 0.0 is pure logistics."

8. In `app/segmentation.py`, update `generate_event_label()`:
   - Change return type from `str` to `tuple[str, float]` (label, significance)
   - Parse JSON response; if significance missing, default to 1.0
   - Update max_tokens from 50 to 100 (to accommodate JSON response)

## Constraints
- Do NOT modify: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/db.py`, `app/clustering.py`
- Do NOT change: The overall pipeline flow in granola.py or telegram.py (those are wired in later sessions)
- Do NOT add: New API endpoints, new tables, new dependencies
- Preserve backward compatibility: `segment_transcript()` must still return `list[Segment]`; callers that don't use the new fields should not break

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write in `tests/test_segmentation.py`:
  1. Segment dataclass has start_line, end_line, significance fields
  2. segment_transcript parses significance from response
  3. segment_transcript defaults significance to 1.0 when missing
  4. segment_transcript clamps out-of-range significance values
  5. filter_by_significance returns segments at or above threshold
  6. filter_by_significance excludes segments below threshold
  7. filter_by_significance returns empty list when all below threshold
  8. filter_by_significance does not mutate input list
  9. dedup_labels returns unchanged when no duplicates
  10. dedup_labels appends (II) to second duplicate
  11. dedup_labels appends (II), (III) for triple duplicates
  12. dedup_labels does not mutate input list
  13. generate_event_label returns (label, significance) tuple
  14. generate_event_label defaults significance to 1.0 when missing from response
- Minimum new test count: 12
- Test command: `python -m pytest tests/test_segmentation.py -x -q`

## Config Validation
Verify that `significance_threshold` is accessible via `get_settings().significance_threshold` and defaults to 0.3 when not set in environment.

## Definition of Done
- [ ] All requirements implemented
- [ ] All existing 166 tests pass
- [ ] ≥12 new tests written and passing
- [ ] Config field accessible with correct default
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| segment_transcript still returns list[Segment] | Existing test_segmentation tests pass |
| generate_event_label callers in telegram.py still work | `python -m pytest tests/test_telegram.py -x -q` |
| Settings loads without new env vars | Test that get_settings() works without SIGNIFICANCE_THRESHOLD set |

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout. See the close-out skill for the
full schema and requirements.

**Write the close-out report to a file:**
docs/sprints/sprint-4/session-1-closeout.md

Do NOT just print the report in the terminal. Create the file, write the
full report (including the structured JSON appendix) to it, and commit it.

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-4/review-context.md`
2. The close-out report path: `docs/sprints/sprint-4/session-1-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_segmentation.py tests/test_telegram.py -x -q`
5. Files that should NOT have been modified: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/db.py`, `app/clustering.py`, `app/granola.py`, `app/telegram.py`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-4/session-1-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the implementation
prompt template instructions.

## Session-Specific Review Focus (for @reviewer)
1. Verify the significance field is parsed correctly from mock Claude responses in tests
2. Verify that missing significance defaults to 1.0 (not 0.0 — default-include, not default-exclude)
3. Verify dedup_labels handles case sensitivity correctly (exact match only, not case-insensitive)
4. Verify the label prompt register instruction matches the design-reference.md Copy Tone section
5. Verify generate_event_label return type change doesn't break any existing callers (check telegram.py imports)

## Sprint-Level Regression Checklist
- [ ] All 166 pre-Sprint 4 tests pass
- [ ] `/events` GET returns valid JSON with existing field schema
- [ ] `/clusters` GET returns valid JSON with existing field schema
- [ ] Telegram webhook processes text messages end-to-end
- [ ] Granola upload processes transcripts end-to-end
- [ ] New config fields have defaults (app starts without them)
- [ ] insert_event() backward compatible
- [ ] segment_transcript() returns valid Segments with new fields
- [ ] dedup_labels and filter_by_significance do not mutate input lists

## Sprint-Level Escalation Criteria
1. Significance score distribution degenerate (>90% same side) → pause, redesign prompt
2. Segmentation prompt returns malformed significance for >30% of segments → redesign prompt
