# Sprint 1, Session 4a: Telegram Webhook Handler

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/main.py`
   - `app/embedding.py`
   - `app/clustering.py`
   - `app/db.py`
2. Run the test baseline:
   Scoped: `python -m pytest tests/test_clustering.py tests/test_embedding.py tests/test_db.py -x -q`
   Expected: ~31 tests, all passing (excluding integration-marked tests)
3. Verify you are on the correct branch: `sprint-1` (or `main`)
4. Verify TELEGRAM_BOT_TOKEN is set

## Objective
Implement the Telegram webhook receiver that validates incoming payloads, extracts text and participant identity, runs the full embed → assign → store pipeline, and handles all edge cases (empty messages, duplicates, non-text messages, API failures). This is the critical integration session that wires together all prior sessions' output.

## Requirements

1. Create `app/telegram.py`:
   - `PARTICIPANT_MAP` — configurable mapping from Telegram username to participant name:
     ```python
     PARTICIPANT_MAP = {
         # Populated from config or hardcoded for v1:
         # "telegram_username": "participant_name"
     }
     ```
     Default: unknown usernames map to "unknown"

   - `extract_message(update: dict) -> tuple[str, str, int] | None`:
     - Parses a Telegram webhook update payload
     - Returns (text, participant_name, update_id) or None if not a text message
     - Maps Telegram username to participant name via PARTICIPANT_MAP
     - Returns None for non-text messages (photos, stickers, voice, etc.)

   - `is_duplicate(update_id: int) -> bool`:
     - Checks if this update_id has already been processed
     - Implementation options: in-memory set (simple for v1), or DB check
     - Document the choice in close-out

   - `process_telegram_update(update: dict) -> dict`:
     - Full pipeline: extract → check duplicate → embed → assign cluster → store in DB
     - Returns a status dict: {"processed": True/False, "reason": "...", "event_id": "..." or None}
     - On embedding failure: raise or return {"processed": False, "reason": "embedding_failed"}
     - On DB failure: raise or return {"processed": False, "reason": "db_failed"}

2. Update `app/main.py`:
   - Add `POST /telegram` endpoint:
     - Accepts raw JSON body (Telegram webhook format)
     - Calls `process_telegram_update()`
     - **Always returns 200** regardless of outcome (prevents Telegram retry storms)
     - On success: 200 with {"ok": True}
     - On skip (empty, duplicate, non-text): 200 with {"ok": True, "skipped": True, "reason": "..."}
     - On embedding failure: 200 with {"ok": False, "error": "embedding_failed"} — but does NOT return 503 to Telegram (503 only for non-Telegram callers)
       Note: The sprint spec says "503 on OpenAI failure" but for the Telegram webhook specifically, we must always return 200. Log the error server-side. If called directly (not from Telegram), 503 is appropriate — but distinguish this in Session 4b integration tests.
   - Ensure seed clusters are populated before the first event arrives (call seed_clusters on startup if not already seeded)

3. Update `requirements.txt`:
   - Add `python-telegram-bot` if needed for type definitions or utilities
   - Or handle raw webhook payloads directly (simpler — Telegram sends plain JSON)
   - Document the choice in close-out

4. Create `tests/test_telegram.py`:
   - Test extract_message with valid text message → returns (text, participant, update_id)
   - Test extract_message with photo message → returns None
   - Test extract_message with empty text → returns None or ("", participant, update_id) — specify behavior
   - Test extract_message maps known username to participant name
   - Test extract_message maps unknown username to "unknown"
   - Test is_duplicate returns False on first call, True on second call with same update_id
   - Test process_telegram_update full pipeline with mocked embedding + DB
   - Test POST /telegram returns 200 on valid message (with mocked pipeline)
   - Test POST /telegram returns 200 on empty message (skipped)

## Constraints
- Do NOT modify: `static/index.html`, any files under `docs/`
- Do NOT modify: `app/embedding.py`, `app/clustering.py` (only import and call them)
- Do NOT modify: `app/db.py` function signatures (only call existing functions)
- Do NOT add: Granola handling (Session 4b)
- Do NOT build: a full Telegram bot framework with command handlers — this is a webhook receiver only
- Telegram webhook always returns 200 — this is a hard requirement

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write: listed in Requirements #4
- Minimum new test count: 8
- Test command: `python -m pytest -x -q`

## Definition of Done
- [ ] Valid Telegram text message → event stored with embedding and cluster_id
- [ ] Empty message → 200, no event, warning logged
- [ ] Duplicate update_id → 200, no duplicate event
- [ ] Non-text message → 200, logged as unsupported, no event
- [ ] Unknown Telegram user → participant = "unknown"
- [ ] POST /telegram always returns 200 (even on internal failures)
- [ ] Seed clusters confirmed present at startup
- [ ] All existing tests still pass
- [ ] All new tests pass
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Sprint-Level)
| Check | How to Verify |
|-------|---------------|
| Health endpoint returns 200 with DB status | `pytest tests/test_health.py` |
| GET /events returns valid JSON | `pytest tests/test_endpoints.py` |
| GET /clusters returns 6 clusters | `pytest tests/test_endpoints.py -k clusters` |
| Embedding module unchanged | `pytest tests/test_embedding.py` |
| Clustering module unchanged | `pytest tests/test_clustering.py` |
| No partial writes on failure | Test in test_telegram.py |
| Telegram endpoint returns 200 on all inputs | `pytest tests/test_telegram.py` |

## Sprint-Level Escalation Criteria
1. Supabase pgvector unavailable → STOP
2. Railway deployment fails 3+ consecutive times → STOP
3. OpenAI embedding dimensions ≠ 1536 → STOP
4. Degenerate cluster assignment (>80% to one cluster) → STOP
5. Cosine similarity uniformly > 0.95 or < 0.1 → STOP
6. Any session exceeds 2× estimated test count → STOP
7. supabase-py requires >20 lines raw SQL for vector ops → escalate
8. **Telegram webhook needs different endpoint structure → escalate** (directly relevant)
9. Compaction in Session 4b → partial close-out + follow-up

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-1/session-4a-closeout.md

**Important for this session's close-out:** Note the idempotency implementation choice (in-memory vs DB) and the Telegram library choice (raw JSON vs python-telegram-bot). These may become DEC entries.

## Tier 2 Review (Mandatory — @reviewer Subagent)
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-1/review-context.md`
2. The close-out report path: `docs/sprints/sprint-1/session-4a-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_telegram.py -x -q`
5. Files that should NOT have been modified: `static/index.html`, `app/embedding.py`, `app/clustering.py`, `app/db.py` (except if seed call was added to startup), anything under `docs/` (except sprint reports)

The @reviewer will write its report to: docs/sprints/sprint-1/session-4a-review.md

## Session-Specific Review Focus (for @reviewer)
1. Verify POST /telegram ALWAYS returns 200 (never 4xx or 5xx to Telegram)
2. Verify no partial writes: if embedding fails, no event row exists
3. Verify duplicate update_id handling is functional
4. Verify unknown Telegram users map to "unknown" participant (not crash)
5. Verify non-text messages are skipped gracefully (not errored)
6. Verify seed clusters are confirmed present before first event processing
7. Verify embedding.py and clustering.py were not modified (only imported)
8. Check that the pipeline order is correct: extract → dedup check → embed → assign → store → increment count
