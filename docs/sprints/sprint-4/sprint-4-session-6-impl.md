# Sprint 4, Session 6: DEF-021 Truncation Fix + Re-seed + Verification

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/segmentation.py` (post-Session 1)
   - `app/granola.py` (post-Session 4a)
   - `scripts/seed_transcript.py` (post-Session 4b)
   - `docs/sprints/sprint-4/sprint-spec.md`
   - The source transcript files: `docs/source/` (list files to identify which transcripts to re-seed)
2. Run the full test suite:
   `python -m pytest tests/ -x -q`
   Expected: all tests passing (166 original + ~51 new ≈ 217)
3. Verify you are on branch: `sprint-4`
4. Verify migration has been applied to production: `scripts/migrate_sprint4.sql` run on production Supabase

## Objective
Find and fix the 10,243-char truncation bug (DEF-021). Re-seed production with all Sprint 4 changes. Verify data quality improvements.

## Requirements

### Part 1: DEF-021 Investigation

1. **Identify the truncation source.** Three segments in the Sprint 3.5 re-seed were truncated at exactly 10,243 characters, ending mid-sentence: "Bicameral Mind Left Right", "Myths Scientific Truth Storytelling", "Network state violence discussion".

2. **Investigation path** — check these in order:
   a. `app/segmentation.py` — `segment_transcript()`: when extracting `segment_text = "\n".join(lines[start - 1 : end])`, is there any truncation?
   b. `SEGMENTATION_PROMPT` — does the Claude response itself truncate? Check `max_tokens=4096` in the API call. If the JSON response is cut off at 4096 tokens, the last segment's text boundaries may be fine but the segment's extracted text from the original lines is long.
   c. The actual culprit is likely that the segment _text_ (extracted from original lines) is fine, but something downstream truncates the `note` field. Check: `insert_event(note=segment.text, ...)` — is there a limit on the `note` TEXT field? Postgres TEXT has no limit, but check if the Supabase client or REST API has a payload size limit.
   d. Check the OpenAI embedding API: does `embed_text()` truncate input? text-embedding-3-small has an 8191 token input limit — 10,243 chars at ~4 chars/token ≈ 2,561 tokens, well within limit. Unlikely.
   e. Check if 10,243 is a Python string operation artifact (unlikely but check).

3. **Fix** — once identified, apply the fix. This may involve:
   - Increasing `max_tokens` on the segmentation API call
   - Removing a truncation in the pipeline
   - Adjusting a payload limit

4. **Write a test** that verifies the truncation limit no longer exists.

### Part 2: Re-seed Production

5. **Clear production events.** Delete all events from the production database. (Clusters will be re-created by seed_clusters + dynamic creation.)

6. **Clear production clusters** (except seed clusters, which will be re-seeded by the startup script). Or: clear all clusters and let seed_clusters() + dynamic creation rebuild everything.

7. **Clear raw_inputs** (if any exist from testing).

8. **Re-seed** using `scripts/seed_transcript.py` with both transcripts:
   - First, do a dry-run to verify significance scores and filtering
   - Then run live
   - Record: total segments, filtered segments, events created, clusters created (seed + dynamic), any naming events

### Part 3: Verification

9. **Verify data quality improvements against Sprint 4 acceptance criteria:**
   - Logistics noise filtered: segments like "Session Ending Voice Identification", "Technical audio video setup" should not appear as events
   - Labels in marginalia register: no ALL-CAPS keyword style, labels read as propositions
   - No duplicate labels in the data
   - New clusters created for below-threshold events: The Table should no longer hold 68% of events
   - Previously truncated segments now have full content (> 10,243 chars)
   - All transcripts stored in raw_inputs with valid references
   - Events have valid raw_input_id, start_line, end_line

10. **Print a summary report** to stdout:
    - Event count per cluster (compare to Sprint 3.5 distribution)
    - Number of dynamic clusters created
    - Number of events filtered by significance
    - Any "The Unnamed" clusters (below naming threshold)
    - Sample labels (first 10) for register quality check

## Constraints
- Do NOT modify: `app/main.py`, `app/myth.py`, `static/index.html`
- The re-seed is a destructive operation on production data. Be explicit about what is being deleted before deleting.
- Do not delete seed cluster definitions from code — only production DB rows.

## Test Targets
After implementation:
- All existing tests pass
- New tests:
  1. Regression test: a segment text of 15,000+ chars is not truncated through the pipeline
  2. Test for the specific fix (depends on root cause)
  3. Verification that re-seeded data has no truncated segments
- Minimum new test count: 2
- Full test suite: `python -m pytest tests/ -x -q`

## Definition of Done
- [ ] DEF-021 root cause identified and documented
- [ ] Fix applied and tested
- [ ] Production re-seeded with Sprint 4 changes
- [ ] Verification report printed showing improved data quality
- [ ] The Table cluster no longer holds >50% of events
- [ ] No truncated segments in re-seeded data
- [ ] All transcripts in raw_inputs table
- [ ] All new tests pass
- [ ] Full test suite passes
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| All pre-Sprint 4 tests still pass | Full suite |
| /events returns valid data after re-seed | curl production URL |
| /clusters returns valid data | curl production URL |
| Frontend loads without errors | Visit production URL in browser |
| Myth generation works for new clusters | Test /myth endpoint for a dynamic cluster |

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-4/session-6-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer subagent.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-4/review-context.md`
2. The close-out report path: `docs/sprints/sprint-4/session-6-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (final session — full suite): `python -m pytest tests/ -x -q`
5. Files that should NOT have been modified: `app/main.py`, `app/myth.py`, `static/index.html`

The @reviewer will write its report to: docs/sprints/sprint-4/session-6-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the implementation
prompt template instructions.

## Session-Specific Review Focus (for @reviewer)
1. Verify DEF-021 root cause is documented in the close-out (not just the fix)
2. Verify the truncation test is meaningful (tests a segment longer than the old limit)
3. Verify re-seed data shows improved cluster distribution
4. Verify no logistics noise segments appear as events
5. Verify raw_inputs table has entries for all re-seeded transcripts
6. Full test suite passes (this is the final session)

## Sprint-Level Regression Checklist
- [ ] Full test suite passes
- [ ] /events GET returns valid JSON
- [ ] /clusters GET returns valid JSON
- [ ] /myth POST works for seed and dynamic clusters
- [ ] Telegram webhook works end-to-end
- [ ] Granola upload works end-to-end
- [ ] Frontend renders without errors
- [ ] Seed cluster centroids present
- [ ] Dynamic clusters exist with correct is_seed=False

## Sprint-Level Escalation Criteria
1. DEF-021 is a platform limit → escalate for architectural decision
2. Cluster explosion (>15 new clusters) → tune threshold
3. Significance distribution degenerate → redesign prompt
4. Archetype names fail Copy Tone at ≥50% → redesign prompt
