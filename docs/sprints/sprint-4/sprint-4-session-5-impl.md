# Sprint 4, Session 5: Telegram Pipeline Integration

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/telegram.py`
   - `app/segmentation.py` (post-Session 1 — generate_event_label returns tuple)
   - `app/clustering.py` (post-Session 3 — assign_or_create_cluster)
   - `app/db.py` (post-Session 2 — insert_raw_input)
   - `docs/sprints/sprint-4/sprint-spec.md`
2. Run scoped test baseline:
   `python -m pytest tests/test_telegram.py -x -q`
   Expected: all passing
3. Verify you are on branch: `sprint-4`

## Objective
Wire raw_input storage, significance filtering, and new-cluster creation into the Telegram pipeline. Every Telegram message gets stored in raw_inputs. Only significant messages become events.

## Requirements

1. In `app/telegram.py`, update `process_telegram_update()` to follow this pipeline:
   1. **Extract message** — Same as before: `extract_message(update)` returns (text, participant, update_id)
   2. **Check duplicate** — Same as before: `is_duplicate(update_id)` — keep this BEFORE any API calls to avoid wasting resources
   3. **Generate label + significance** — Call `generate_event_label(text)` which now returns `(label, significance)`. Handle the updated return type.
   4. **Store in raw_inputs** — Call `insert_raw_input(text=text, source="telegram", source_metadata={"update_id": update_id, "participant": participant})`. Save `raw_input_id`.
   5. **Significance check** — If significance < `get_settings().significance_threshold`: return `{"processed": False, "reason": "below_significance", "event_id": None, "raw_input_id": raw_input_id}`
   6. **Embed** — Same as before
   7. **Assign or create cluster** — Call `assign_or_create_cluster()` instead of `assign_cluster()`
   8. **Insert event** — Call `insert_event()` with `raw_input_id=raw_input_id`, `label=label`
   9. **Post-insert** — `increment_event_count()`, then `maybe_name_cluster(cluster_id)`, then `compute_xs()`
   10. Return result dict (add `raw_input_id` to the return dict)

2. Update imports:
   - Add: `assign_or_create_cluster` from `app.clustering`
   - Add: `insert_raw_input` from `app.db`
   - Add: `maybe_name_cluster` from `app.archetype_naming`
   - Add: `get_settings` from `app.config`
   - Remove: `assign_cluster` from `app.clustering` (replaced by assign_or_create_cluster)

3. Handle the `generate_event_label()` return type change:
   - Old: returns `str`
   - New: returns `tuple[str, float]` (label, significance)
   - Update the call site and the fallback path (when label generation fails, default significance to 1.0 so the message is included)

4. Error handling for maybe_name_cluster: wrap in try/except, log warning on failure, do not block pipeline.

5. Error handling for insert_raw_input: wrap in try/except. If raw_input storage fails, log warning but continue processing the message (raw_input storage is non-blocking).

## Constraints
- Do NOT modify: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/segmentation.py`, `app/clustering.py`, `app/db.py`, `app/granola.py`, `scripts/seed_transcript.py`
- Do NOT change: The `extract_message()` or `is_duplicate()` functions
- Do NOT change: The overall return dict structure for `process_telegram_update()` (existing keys must remain; `raw_input_id` is additive)

## Test Targets
After implementation:
- Existing tests: all must still pass (update mocks for new generate_event_label return type)
- New/updated tests in `tests/test_telegram.py`:
  1. process_telegram_update stores message in raw_inputs
  2. process_telegram_update below-significance message: stored in raw_inputs, no event created, reason="below_significance"
  3. process_telegram_update above-significance: creates event with raw_input_id
  4. process_telegram_update handles generate_event_label tuple return
  5. process_telegram_update uses assign_or_create_cluster
  6. process_telegram_update calls maybe_name_cluster after insert
  7. process_telegram_update label generation fallback uses significance 1.0
- Minimum new test count: 6
- Test command: `python -m pytest tests/test_telegram.py -x -q`

## Definition of Done
- [ ] All requirements implemented
- [ ] All existing tests pass (mocks updated)
- [ ] ≥6 new tests written and passing
- [ ] Pipeline flow: extract → dedup → label+sig → store raw → filter → embed → assign/create → insert → name
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| process_telegram_update still returns dict with processed, reason, event_id | Existing tests |
| Duplicate detection still works | Existing is_duplicate tests |
| Label generation fallback still works | Test with mocked API failure |
| /telegram endpoint still works | `python -m pytest tests/test_endpoints.py -x -q` |

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-4/session-5-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer subagent.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-4/review-context.md`
2. The close-out report path: `docs/sprints/sprint-4/session-5-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_telegram.py tests/test_endpoints.py -x -q`
5. Files that should NOT have been modified: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/segmentation.py`, `app/clustering.py`, `app/db.py`, `app/granola.py`, `scripts/seed_transcript.py`

The @reviewer will write its report to: docs/sprints/sprint-4/session-5-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the implementation
prompt template instructions.

## Session-Specific Review Focus (for @reviewer)
1. Verify raw_input is stored BEFORE significance check (message always saved, even if below threshold)
2. Verify dedup check is BEFORE label generation (avoid wasting an API call on duplicates)
3. Verify label generation fallback sets significance to 1.0 (include by default on failure)
4. Verify raw_input storage failure is non-blocking (try/except with warning)
5. Verify the old assign_cluster import is removed
6. Verify return dict includes raw_input_id for both processed and below_significance cases

## Sprint-Level Regression Checklist
- [ ] All pre-Sprint 4 tests pass
- [ ] Telegram webhook processes messages end-to-end
- [ ] event_date, participants, xs populated on new events
- [ ] Duplicate detection still works

## Sprint-Level Escalation Criteria
1. Significance score distribution degenerate → pause, redesign prompt
2. Cluster explosion → tune threshold
