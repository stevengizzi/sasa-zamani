# Sprint 1, Session 4b: Granola Parser + Integration Tests

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/main.py`
   - `app/telegram.py`
   - `app/embedding.py`
   - `app/clustering.py`
   - `app/db.py`
2. Run the test baseline:
   Scoped: `python -m pytest tests/test_telegram.py tests/test_endpoints.py -x -q`
   Expected: ~21 tests, all passing
3. Verify you are on the correct branch: `sprint-1` (or `main`)

**Compaction warning:** This session scores 21 (Critical). If you feel context degrading, STOP, write a partial close-out, and escalate per criteria #9. Do not push through compaction.

## Objective
Implement Granola transcript parsing with speaker attribution, the POST /granola endpoint wired to the embed → assign → store pipeline, and comprehensive end-to-end integration tests covering both input modalities.

## Requirements

1. Create `app/granola.py`:
   - `parse_transcript(transcript: str) -> list[dict]`:
     - Parses a Granola-format transcript into segments
     - Granola format: plain text with speaker labels like "Jessie: ...\n\nEmma: ..."
     - Each segment: {"text": "...", "participant": "jessie"|"emma"|"steven"|"shared"}
     - Participant names normalized to lowercase
     - If no speaker labels detected: single segment with participant = "shared"
     - Empty transcript: returns empty list
   - `SPEAKER_MAP` — mapping from transcript speaker names to participant names:
     ```python
     SPEAKER_MAP = {
         "Jessie": "jessie",
         "Emma": "emma",
         "Steven": "steven",
         # Add common variations if needed
     }
     ```
     Default for unknown speakers: use the speaker name lowercased

   - `process_granola_upload(transcript: str) -> list[dict]`:
     - Full pipeline: parse → embed each segment → assign cluster → store each event
     - Source field set to "granola" for all events
     - Returns list of {"event_id": "...", "participant": "...", "cluster_name": "..."} for each stored event
     - On empty transcript: raises ValueError("Empty transcript")
     - On embedding failure for any segment: rolls back ALL events from this transcript (no partial upload)

2. Update `app/main.py`:
   - Add `POST /granola` endpoint:
     - Accepts JSON body: `{"transcript": "..."}` (or use the GranolaRequest model from Session 2b)
     - Calls `process_granola_upload()`
     - Returns 200 with list of created events on success
     - Returns 400 with error message on empty transcript
     - Returns 503 on embedding or DB failure

3. Create `tests/test_granola.py`:
   - Test parse_transcript with multi-speaker transcript → correct segments and attribution
   - Test parse_transcript with single-speaker transcript → one segment
   - Test parse_transcript with no speaker labels → single segment, participant = "shared"
   - Test parse_transcript with empty string → empty list
   - Test parse_transcript handles varied spacing and formatting
   - Test SPEAKER_MAP contains all three participants
   - Test process_granola_upload with mocked embedding + DB → correct number of stored events

   **Sample test transcript:**
   ```
   Jessie: I had the strangest dream last night about crossing a bridge that kept extending.

   Emma: That reminds me of the conversation we had about thresholds. The food was incredible at that dinner, by the way.

   Steven: I've been writing about exactly this — the way memory reshapes when you try to pin it down.
   ```
   Expected: 3 segments, attributed to jessie, emma, steven respectively.

4. Create `tests/test_integration.py` — end-to-end pipeline tests:
   **These tests exercise the full pipeline through HTTP endpoints, not internal functions.**

   - **Telegram pipeline test:**
     - POST /telegram with a valid webhook payload (mocked or real format)
     - GET /events → verify new event appears with correct fields
     - GET /clusters → verify event_count incremented on the assigned cluster
   - **Granola pipeline test:**
     - POST /granola with sample multi-speaker transcript
     - GET /events → verify all parsed events appear with correct participants
     - GET /events?participant=jessie → verify filter works with Granola-sourced events
   - **Cross-source test:**
     - Send events via both Telegram and Granola
     - GET /events → verify events from both sources appear
     - Verify source field distinguishes "telegram" from "granola"
   - **Empty state test:**
     - GET /events on fresh DB → empty list
     - GET /clusters → 6 seed clusters with event_count = 0
   - **Cluster assignment sanity test:**
     - Send a food-related message via Telegram (e.g., "We cooked dinner together and shared stories")
     - Verify it's assigned to "The Table" cluster (or at least, verify the similarity score is highest for The Table)
     - This is not a hard assertion (embeddings may surprise us) — log the result for RSK-001 evaluation

   **Test strategy for integration tests:**
   - Use the FastAPI test client (httpx)
   - Require a live Supabase connection (or a test DB)
   - Mock the OpenAI API with predictable embeddings for deterministic assertions
   - Mark with `@pytest.mark.integration` if they require external services
   - One fully-live test (real OpenAI + real Supabase) marked `@pytest.mark.live`

## Constraints
- Do NOT modify: `static/index.html`, any files under `docs/`
- Do NOT modify: `app/embedding.py`, `app/clustering.py`, `app/telegram.py`, `app/db.py` — only import and call them
- Do NOT add: any endpoints beyond POST /granola
- Do NOT add: authentication, rate limiting, or media handling
- If compaction occurs: STOP, write partial close-out, escalate per criteria #9

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write: listed in Requirements #3 and #4
- Minimum new test count: 12
- Test command (unit): `python -m pytest -x -q`
- Test command (integration): `python -m pytest -x -q --run-integration`
- Full suite for close-out: `python -m pytest -x -q`

## Definition of Done
- [ ] Granola parser correctly attributes multi-speaker transcripts
- [ ] No-speaker transcripts produce "shared" participant
- [ ] Empty transcript → 400 error
- [ ] POST /granola stores events with source="granola"
- [ ] Integration tests confirm Telegram pipeline end-to-end
- [ ] Integration tests confirm Granola pipeline end-to-end
- [ ] Integration tests confirm cross-source events appear together
- [ ] Cluster assignment sanity test logged (RSK-001 data point)
- [ ] All existing tests still pass
- [ ] All new tests pass
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Sprint-Level — FULL CHECK, FINAL SESSION)
| Check | How to Verify |
|-------|---------------|
| Health endpoint returns 200 with DB status | `pytest tests/test_health.py` |
| GET /events returns valid JSON on empty DB | `pytest tests/test_endpoints.py -k "events and empty"` |
| GET /events excludes embedding vectors | Verify no "embedding" key in response |
| GET /clusters returns exactly 6 seed clusters | `pytest tests/test_endpoints.py -k clusters` or integration test |
| GET /clusters excludes centroid embeddings | Verify no "centroid_embedding" key in response |
| No partial writes on embedding failure | `pytest tests/test_telegram.py -k failure` |
| Telegram webhook always returns 200 | `pytest tests/test_telegram.py -k "200"` |
| Duplicate update_id prevention | `pytest tests/test_telegram.py -k duplicate` |
| Cluster assignment is deterministic | `pytest tests/test_clustering.py -k deterministic` |
| Seed centroids are non-null 1536-dim | `pytest tests/test_clustering.py -k seed` |
| Participant filter is case-insensitive | `pytest tests/test_endpoints.py -k participant` |

## Sprint-Level Escalation Criteria
1. Supabase pgvector unavailable → STOP
2. Railway deployment fails 3+ consecutive times → STOP
3. OpenAI embedding dimensions ≠ 1536 → STOP
4. Degenerate cluster assignment (>80% to one cluster) → STOP
5. Cosine similarity uniformly > 0.95 or < 0.1 → STOP
6. Any session exceeds 2× estimated test count → STOP
7. supabase-py requires >20 lines raw SQL for vector ops → escalate
8. Telegram webhook needs different endpoint structure → escalate
9. **Compaction in Session 4b → partial close-out + follow-up** (THIS SESSION)

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-1/session-4b-closeout.md

**Important for this session's close-out:**
- Include the cluster assignment sanity test results (which cluster did the food message go to? what were the similarity scores?)
- Include total test count for the sprint
- Note any RSK-001 observations from integration testing
- This is the final session — the close-out should reflect sprint-level status

## Tier 2 Review (Mandatory — @reviewer Subagent) — FINAL SESSION
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-1/review-context.md`
2. The close-out report path: `docs/sprints/sprint-1/session-4b-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: **FULL SUITE** `python -m pytest -x -q` (final session uses full suite)
5. Files that should NOT have been modified: `static/index.html`, `app/embedding.py`, `app/clustering.py`, `app/telegram.py`, `app/db.py`, anything under `docs/` (except sprint reports)

The @reviewer will write its report to: docs/sprints/sprint-1/session-4b-review.md

## Session-Specific Review Focus (for @reviewer)
1. Verify parse_transcript handles the three formats: multi-speaker, single-speaker, no-speaker
2. Verify POST /granola returns 400 on empty transcript (not 200 or 500)
3. Verify all events from Granola have source="granola"
4. Verify no modifications to embedding.py, clustering.py, telegram.py, or db.py
5. Verify integration tests cover both input modalities end-to-end
6. Verify cluster assignment sanity test is logged in close-out (RSK-001 data)
7. Run full regression checklist — this is the final session
8. Verify total test count is reasonable (~57 estimated, flag if >100)
