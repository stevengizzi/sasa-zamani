# Sprint 3.5, Session S2b: Telegram Label Generation

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/telegram.py` (current implementation)
   - `app/segmentation.py` (for `generate_event_label` function)
2. Run scoped test baseline:
   ```
   python -m pytest tests/test_telegram.py -x -q
   ```
   Expected: all passing (full suite confirmed by S2a close-out)
3. Verify you are on the correct branch: `main`

## Objective
Add Claude-generated 3-5 word summary labels for Telegram events, replacing `text[:80]`, with graceful fallback on failure.

## Requirements

1. **In `app/telegram.py` — add label generation:**

   a. Import `generate_event_label` and `SegmentationError` from `app.segmentation`.

   b. In `process_telegram_update()`, after extracting message text and before calling `insert_event()`:
   ```python
   try:
       label = generate_event_label(text)
   except (SegmentationError, Exception) as exc:
       logger.warning("Label generation failed: %s — falling back to text[:80]", exc)
       label = text[:80]
   ```

   c. Use the generated `label` in the `insert_event()` call (replacing the current `text[:80]` pattern).

   d. The event must still be inserted even if label generation fails. Label failure is non-blocking.

## Constraints
- Do NOT modify: `app/config.py`, `app/embedding.py`, `app/myth.py`, `app/clustering.py`, `app/main.py`, `app/db.py`, `app/models.py`, `app/granola.py`, `app/segmentation.py`, `static/index.html`, `scripts/seed_transcript.py`, `tests/conftest.py`
- Do NOT change: the event insertion, increment, or xs computation logic
- Do NOT change: the dedup logic, the extract_message logic, or the return value contract
- The fallback to `text[:80]` must be silent to the caller (return value unchanged)

## Test Targets
After implementation:
- Existing tests: all must still pass (some may need mock updates if they assert on `label`)
- New tests to write:
  1. `test_telegram_uses_llm_label` — mock `generate_event_label` returning "Morning coffee ritual", verify `insert_event` called with `label="Morning coffee ritual"`
  2. `test_telegram_label_failure_falls_back` — mock `generate_event_label` raising `SegmentationError`, verify `insert_event` called with `label=text[:80]`
  3. `test_telegram_label_content_passed_through` — verify the label from `generate_event_label` is the exact value passed to `insert_event(label=...)`
- Minimum new test count: 3
- Test command: `python -m pytest tests/test_telegram.py -x -q`

## Definition of Done
- [ ] `process_telegram_update()` calls `generate_event_label()` for label generation
- [ ] Label failure falls back to `text[:80]` with warning log
- [ ] Event insertion proceeds regardless of label generation outcome
- [ ] All existing tests pass
- [ ] 3 new tests written and passing
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| Telegram happy path unchanged | Existing process_telegram_update tests pass |
| Dedup logic unchanged | Existing is_duplicate tests pass |
| extract_message logic unchanged | Existing extract_message tests pass |
| Return value contract unchanged | Existing tests verify `{"processed": True, ...}` |
| Label fallback works | New test verifies text[:80] on failure |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-3.5/session-s2b-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3.5/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3.5/session-s2b-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (scoped): `python -m pytest tests/test_telegram.py -x -q`
5. Files that should NOT have been modified: `app/config.py`, `app/embedding.py`, `app/myth.py`, `app/clustering.py`, `app/main.py`, `app/db.py`, `app/models.py`, `app/granola.py`, `app/segmentation.py`, `static/index.html`, `scripts/seed_transcript.py`, `tests/conftest.py`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3.5/session-s2b-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the standard protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify `generate_event_label` is imported from `app.segmentation` (not reimplemented)
2. Verify fallback is `text[:80]` (not empty string, not None, not truncated differently)
3. Verify the try/except catches both `SegmentationError` and general `Exception` (API could throw unexpected errors)
4. Verify the warning log includes the error message for debugging
5. Verify the event insertion call is OUTSIDE the label try/except (label failure cannot block insertion)
6. Verify no changes to dedup, extract_message, or return contract

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Pre-sprint: 147 passed, 3 skipped, 3 pre-existing errors
- Hard floor: ≥118 pass

### Critical Invariants
- Telegram pipeline inserts events
- Dedup logic unchanged
- Return value contract unchanged

## Sprint-Level Escalation Criteria
1. Test pass count drops below 118
2. Label generation adds > 3s latency to Telegram processing → discuss async option
