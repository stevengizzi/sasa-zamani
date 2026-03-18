# Sprint 1, Session 2a: Database Connection + Schema Creation

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/main.py`
   - `app/config.py`
   - `docs/architecture.md`
2. Run the test baseline:
   Scoped: `python -m pytest tests/test_health.py -x -q`
   Expected: 5 tests, all passing
3. Verify you are on the correct branch: `sprint-1` (or `main`)
4. Verify Supabase project exists and is accessible with SUPABASE_URL and SUPABASE_KEY

## Objective
Create the Supabase database client, establish the events and clusters tables with pgvector support, and implement basic CRUD operations. Update the health endpoint to report database connection status.

## Requirements

1. Update `app/config.py`:
   - No new fields needed (SUPABASE_URL and SUPABASE_KEY already defined)

2. Update `requirements.txt`:
   - Add `supabase` (Python client)
   - Add `vecs` or equivalent if needed for pgvector operations (evaluate whether supabase-py handles vector types natively — if not, use raw SQL via `supabase.rpc()` or `supabase.postgrest`)

3. Create `app/db.py` — Supabase client module:
   - `get_db()` function returning initialized Supabase client (singleton via settings)
   - `ensure_schema()` function that creates tables if they don't exist (idempotent):
     - Enable pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector`
     - `events` table: id (UUID, default gen_random_uuid()), label (text), note (text), participant (text), embedding (vector(1536)), cluster_id (UUID, nullable FK to clusters), created_at (timestamptz, default now()), source (text)
     - `clusters` table: id (UUID, default gen_random_uuid()), name (text, unique), centroid_embedding (vector(1536)), event_count (integer, default 0), last_updated (timestamptz, default now())
   - `insert_event(label, note, participant, embedding, cluster_id, source)` → returns inserted event
   - `get_events(participant=None)` → returns list of events (without embedding field), filtered by participant if provided (case-insensitive)
   - `get_clusters()` → returns list of clusters (without centroid_embedding field)
   - `insert_cluster(name, centroid_embedding)` → returns inserted cluster
   - `get_cluster_centroids()` → returns list of (cluster_id, centroid_embedding) tuples for assignment logic
   - `increment_event_count(cluster_id)` → increments event_count for a cluster
   - `check_connection()` → returns True/False for health check

4. Update `app/main.py`:
   - Update `GET /health` to call `check_connection()` and return `{"status": "healthy", "database": "connected"}` or `{"status": "degraded", "database": "disconnected"}`
   - Call `ensure_schema()` on startup (in a lifespan handler or startup event)

5. Create `tests/test_db.py`:
   - Test check_connection returns True with valid Supabase config
   - Test ensure_schema is idempotent (calling twice doesn't error)
   - Test insert_event and get_events round-trip
   - Test get_events with participant filter
   - Test get_events returns empty list when no events exist
   - Test insert_cluster and get_clusters round-trip
   - Test get_cluster_centroids returns centroid embeddings
   - Test increment_event_count

   **Note on test strategy:** These tests need a database. Options:
   - Use real Supabase with a test-prefixed table name (simplest for v1)
   - Mock the Supabase client (faster but less confidence)
   - Choose whichever approach fits the project's testing philosophy, document the choice in close-out

## Constraints
- Do NOT modify: `static/index.html`, any files under `docs/`
- Do NOT create: any API endpoints beyond updating /health (GET /events and GET /clusters are Session 2b)
- Do NOT add: embedding or clustering logic (Sessions 3a, 3b)
- Do NOT add: Telegram or Granola handling (Sessions 4a, 4b)
- Keep DB functions generic — they accept embeddings as lists of floats without knowing how they were generated

## Test Targets
After implementation:
- Existing tests: all must still pass (test_health.py)
- New tests to write: listed in Requirements #5
- Minimum new test count: 8
- Test command: `python -m pytest -x -q`

## Definition of Done
- [ ] All requirements implemented
- [ ] Supabase tables created with correct schema
- [ ] pgvector extension enabled and vector column works
- [ ] Health endpoint reports database connection status
- [ ] All existing tests still pass
- [ ] All new tests pass
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Sprint-Level)
| Check | How to Verify |
|-------|---------------|
| Health endpoint returns 200 | `python -m pytest tests/test_health.py -k health` |
| App starts cleanly with all env vars | `uvicorn app.main:app` starts without error |
| App fails fast on missing env vars | Remove SUPABASE_URL, verify startup error |
| Health endpoint now reports DB status | `curl /health` includes "database" field |

## Sprint-Level Escalation Criteria
1. Supabase pgvector unavailable → STOP
2. Railway deployment fails 3+ consecutive times → STOP
3. OpenAI embedding dimensions ≠ 1536 → STOP
4. Degenerate cluster assignment (>80% to one cluster) → STOP
5. Cosine similarity uniformly > 0.95 or < 0.1 → STOP
6. Any session exceeds 2× estimated test count → STOP
7. supabase-py requires >20 lines raw SQL for vector ops → escalate
8. Telegram webhook needs different endpoint structure → escalate
9. Compaction in Session 4b → partial close-out + follow-up

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout. See the close-out skill for the
full schema and requirements.

**Write the close-out report to a file:**
docs/sprints/sprint-1/session-2a-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-1/review-context.md`
2. The close-out report path: `docs/sprints/sprint-1/session-2a-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_db.py -x -q`
5. Files that should NOT have been modified: `static/index.html`, anything under `docs/` (except sprint reports)

The @reviewer will write its report to: docs/sprints/sprint-1/session-2a-review.md

## Session-Specific Review Focus (for @reviewer)
1. Verify events table has embedding column of type vector(1536)
2. Verify clusters table has centroid_embedding column of type vector(1536)
3. Verify ensure_schema() is idempotent (uses IF NOT EXISTS)
4. Verify get_events() excludes embedding from returned data
5. Verify get_clusters() excludes centroid_embedding from returned data
6. Verify check_connection() handles Supabase being down gracefully (returns False, not crash)
7. Verify escalation criteria #7: check how much raw SQL is needed for pgvector operations
