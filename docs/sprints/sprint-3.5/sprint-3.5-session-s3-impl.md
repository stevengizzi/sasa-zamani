# Sprint 3.5, Session S3: Re-Seed + Label Backfill + Verification

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `scripts/seed_transcript.py` (updated in S2a — understand new segmentation flow)
   - `app/segmentation.py` (for `generate_event_label` function used in backfill)
   - `app/db.py` (for event query/update patterns)
2. Run full test suite:
   ```
   python -m pytest -n auto -q
   ```
   Expected: all passing (full suite confirmed by S2b close-out — count will be higher than 147 due to new tests from S1a/S1b/S2a/S2b)
3. Verify you are on the correct branch: `main`

## Objective
Create a label backfill script for existing Telegram events, then execute the production re-seed: delete old granola events, re-seed with thematic segmentation, backfill Telegram labels, and verify everything on production.

## Requirements

1. **Create `scripts/backfill_labels.py`:**

   A small utility script that:
   - Fetches all events where `source = 'telegram'` from Supabase
   - For each event, calls `generate_event_label(event["note"])` to get a new label
   - Updates the event's `label` field via `get_db().table("events").update({"label": label}).eq("id", event_id).execute()`
   - Prints progress: which events were updated, old label vs new label
   - Handles label generation failure per-event (log warning, skip, continue)
   - Loads environment from `.env` via `dotenv`

   Usage:
   ```
   python -m scripts.backfill_labels
   ```

2. **Create `tests/test_backfill_labels.py`:**
   - One test verifying the backfill flow with mocked DB and label generation

3. **Execute production re-seed (manual steps, documented in close-out):**

   a. Delete existing granola events:
   ```sql
   DELETE FROM events WHERE source = 'granola';
   ```

   b. Reset cluster event_counts:
   ```sql
   UPDATE clusters SET event_count = 0;
   ```

   c. Re-seed March 17 transcript:
   ```bash
   python -m scripts.seed_transcript \
     --file docs/source/3-17-granola-transcript.md \
     --speaker-map '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}' \
     --date 2026-03-17
   ```

   d. Re-seed March 18 transcript:
   ```bash
   python -m scripts.seed_transcript \
     --file docs/source/3-18-granola-transcript.md \
     --speaker-map '{"Speaker B": "emma", "Speaker C": "jessie", "Speaker F": "steven"}' \
     --date 2026-03-18
   ```

   e. Backfill Telegram labels:
   ```bash
   python -m scripts.backfill_labels
   ```

   f. Verify event counts in Supabase:
   ```sql
   SELECT COUNT(*), source FROM events GROUP BY source;
   SELECT COUNT(*), participant FROM events GROUP BY participant;
   SELECT c.name, c.event_count FROM clusters c ORDER BY c.event_count DESC;
   ```

4. **Verify on production URL:**
   - Both views render with re-seeded data
   - Event detail panels show LLM-generated labels (not raw transcript text)
   - Participant colors correct
   - Archetype panels show myth text
   - No console errors

## Constraints
- Do NOT modify: any existing `app/` files, `scripts/seed_transcript.py`, `static/index.html`, existing test files
- The backfill script is a one-time utility. It does not need to be robust against concurrent writes or large datasets.

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests:
  1. `test_backfill_updates_label` — mock `get_db` and `generate_event_label`, verify update called with new label
- Minimum new test count: 1
- Test command: `python -m pytest -n auto -q` (final session — full suite)

## Definition of Done
- [ ] `scripts/backfill_labels.py` exists and runs
- [ ] `tests/test_backfill_labels.py` exists and passes
- [ ] All existing granola events deleted from production
- [ ] Both transcripts re-seeded with thematic segmentation
- [ ] Telegram events backfilled with LLM labels
- [ ] Event counts verified in Supabase
- [ ] Visual verification on production URL
- [ ] All tests pass (full suite)
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| No existing files modified | `git diff --name-only` shows only new files + docs |
| Full test suite passes | `python -m pytest -n auto -q` |
| Production URL loads | Visual check |
| Both views render | Visual check |
| Labels are readable | Event detail panel shows short summary, not transcript fragment |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**The close-out for this session should additionally include:**
- Final event counts (total, per-source, per-participant, per-cluster)
- Segmentation ratio comparison: how many thematic segments vs. original speaker turns for each transcript
- Sample labels: 5 example labels from the re-seeded data
- Any observations about segmentation quality

**Write the close-out report to a file:**
docs/sprints/sprint-3.5/session-s3-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3.5/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3.5/session-s3-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (full suite — final session): `python -m pytest -n auto -q`
5. Files that should NOT have been modified: all existing `app/` files, `scripts/seed_transcript.py`, `static/index.html`, existing test files

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3.5/session-s3-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the standard protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify `backfill_labels.py` handles per-event failure gracefully (skip, not abort)
2. Verify no existing `app/` or `scripts/` files were modified (only new files)
3. Verify the close-out includes event count comparison and sample labels
4. Check segmentation ratio: is it within the 50%-150% escalation bounds?
5. Verify the re-seed commands used correct `--date` values (2026-03-17 and 2026-03-18)
6. Full test suite passes

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Pre-sprint: 147 passed, 3 skipped, 3 pre-existing errors
- Hard floor: ≥118 pass

### Critical Invariants
- All existing tests pass
- Production URL renders both views
- Labels readable in detail panels
- No console errors

## Sprint-Level Escalation Criteria
1. Segmentation ratio < 50% or > 150% of original speaker-turn count
2. Claude API cost per transcript exceeds $0.50
3. Test pass count drops below 118
4. Segmentation quality is poor on manual review (incoherent segments)
