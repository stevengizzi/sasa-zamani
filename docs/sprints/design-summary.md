# Sprint 1 Design Summary

**Sprint Goal:** Stand up the full backend data pipeline for Sasa/Zamani — from receiving Telegram messages and Granola transcripts, through OpenAI embedding and cluster assignment, to serving events and clusters via REST API. By sprint end, `GET /events` and `GET /clusters` return real data from Supabase, and `POST /telegram` and `POST /granola` process input through the full embed → assign → store pipeline.

**Session Breakdown:**

- Session 1: Project scaffold, configuration system (env vars via Pydantic Settings), FastAPI app skeleton with health endpoint, deploy to Railway.
  - Creates: `app/__init__.py`, `app/main.py`, `app/config.py`, `requirements.txt`, `.env.example`, `Procfile`, `tests/__init__.py`, `tests/conftest.py`, `tests/test_health.py`
  - Modifies: Nothing (greenfield)
  - Integrates: N/A (first session)

- Session 2a: Supabase database connection, schema creation (events table with pgvector, clusters table), basic CRUD operations.
  - Creates: `app/db.py`, `tests/test_db.py`
  - Modifies: `app/config.py` (add DB settings), `requirements.txt` (add supabase-py)
  - Integrates: Session 1's config.py

- Session 2b: Pydantic request/response models, GET /events (with ?participant= filter), GET /clusters endpoints.
  - Creates: `app/models.py`, `tests/test_endpoints.py`
  - Modifies: `app/main.py` (add GET routes)
  - Integrates: Session 2a's db.py

- Session 3a: OpenAI embedding integration — embed_text() function, error handling, mock-friendly architecture for testing.
  - Creates: `app/embedding.py`, `tests/test_embedding.py`
  - Modifies: `app/config.py` (add OpenAI key), `requirements.txt` (add openai)
  - Integrates: Session 1's config.py

- Session 3b: Cluster assignment logic (cosine similarity against centroids, nearest-cluster assignment), seed cluster centroid computation from representative text, seed cluster insertion into DB.
  - Creates: `app/clustering.py`, `tests/test_clustering.py`
  - Modifies: `app/db.py` (seed cluster functions)
  - Integrates: Session 3a's embedding.py, Session 2a's db.py

- Session 4a: Telegram webhook handler — validate payload, extract text + participant, run through embed → assign → store pipeline, idempotency via update_id.
  - Creates: `app/telegram.py`, `tests/test_telegram.py`
  - Modifies: `app/main.py` (add POST /telegram route)
  - Integrates: Sessions 2a/2b (db.py, models.py), 3a/3b (embedding.py, clustering.py)

- Session 4b: Granola transcript parser — speaker attribution, segment extraction, batch embed → assign → store. End-to-end integration tests covering the full pipeline.
  - Creates: `app/granola.py`, `tests/test_granola.py`, `tests/test_integration.py`
  - Modifies: `app/main.py` (add POST /granola route)
  - Integrates: Same pipeline as 4a (db, models, embedding, clustering)

**Key Decisions:**
- DEC-001: Python + FastAPI backend
- DEC-002: Supabase + pgvector for database
- DEC-003: OpenAI text-embedding-3-small (1536 dim)
- DEC-004: Railway deployment
- DEC-006: Telegram bot + Granola upload as v1 input
- DEC-010: Claude myth generation, ancestral register (confirmed — but /myth deferred to Sprint 2)
- DEC-011: Six seed clusters only, dynamic cluster creation deferred

**Scope Boundaries:**
- IN: FastAPI app, Supabase schema (events + clusters with pgvector), OpenAI embedding pipeline, cluster assignment via cosine similarity, Telegram webhook, Granola parser, GET /events, GET /clusters, seed cluster centroids, Railway deployment
- OUT: POST /myth (Sprint 2), frontend changes, dynamic cluster creation, authentication, real-time updates (WebSocket/SSE), event deletion/editing, media attachments in Telegram (text only), HNSW index optimization, rate limiting, admin interface

**Regression Invariants:**
- GET /health returns 200 with DB connection status
- GET /events returns valid JSON even with empty table (empty array, not error)
- GET /clusters always returns exactly 6 seed clusters
- No partial writes: embedding failure → no event stored
- Telegram webhook always returns 200 (prevent retry storms)
- Cosine similarity assignment is correct: assigned cluster has highest similarity among all centroids

**File Scope:**
- Modify: Only files created within this sprint (greenfield)
- Do not modify: `static/index.html` (the prototype frontend — untouched until Sprint 2), any docs/ files (doc-sync handles updates post-sprint)

**Config Changes:**
Environment variables via Pydantic Settings (no YAML config files):

| Env Var | Pydantic Field | Default |
|---------|---------------|---------|
| SUPABASE_URL | supabase_url | (required) |
| SUPABASE_KEY | supabase_key | (required) |
| OPENAI_API_KEY | openai_api_key | (required) |
| TELEGRAM_BOT_TOKEN | telegram_bot_token | (required) |
| CLUSTER_JOIN_THRESHOLD | cluster_join_threshold | 0.3 |

**Test Strategy:**
- Unit tests per module: db, models/endpoints, embedding, clustering, telegram, granola
- Integration tests: full pipeline (input → embed → assign → store → retrieve)
- Mocks for external APIs (OpenAI, Supabase) in unit tests; one live integration test per external API
- Estimated test count: ~55-65 tests total across 7 sessions
  - Session 1: ~5 (health, config)
  - Session 2a: ~8 (DB connection, CRUD, pgvector)
  - Session 2b: ~10 (model validation, endpoint responses, filtering)
  - Session 3a: ~6 (embed function, error handling, mock/live)
  - Session 3b: ~8 (cosine similarity, assignment, seed centroids)
  - Session 4a: ~8 (webhook validation, idempotency, pipeline)
  - Session 4b: ~12 (parser, attribution, integration tests)

**Runner Compatibility:**
- Mode: human-in-the-loop
- Parallelizable sessions: none (strict sequential: 1 → 2a → 2b → 3a → 3b → 4a → 4b)
- Runner config: not generated

**Dependencies:**
- Supabase project created with pgvector extension enabled
- Railway app created and linked to GitHub repo
- Telegram bot created via BotFather (bot token available)
- OpenAI API key available
- GitHub repo exists: https://github.com/stevengizzi/sasa-zamani.git

**Escalation Criteria:**
- Supabase pgvector extension unavailable or incompatible → escalate (blocks all embedding storage)
- OpenAI embedding API returns unexpected dimensions (!= 1536) → escalate (schema mismatch)
- Railway deployment fails on 3+ consecutive attempts → escalate
- Cosine similarity produces degenerate results (all events assigned to same cluster) → escalate (RSK-001 materialized)
- Any session exceeds 2× estimated test count → escalate (scope creep signal)

**Doc Updates Needed:**
- docs/architecture.md: update with actual file paths, actual endpoint signatures, actual schema DDL
- docs/sprint-history.md: add Sprint 1 entry
- docs/decision-log.md: confirm DEC-010 and DEC-011 (remove "[Inferred]" tag)
- docs/risk-register.md: update RSK-001 with actual embedding quality observations
- CLAUDE.md: update with Sprint 1 state, test counts, infrastructure details
- docs/project-knowledge.md, docs/architecture.md, CLAUDE.md: add GitHub repo link (https://github.com/stevengizzi/sasa-zamani.git) so it can always be referenced and cloned

**Artifacts to Generate:**
1. Sprint Spec
2. Specification by Contradiction
3. Session Breakdown (with Creates/Modifies/Integrates per session)
4. Escalation Criteria
5. Regression Checklist
6. Doc Update Checklist
7. Review Context File
8. Implementation Prompts ×7
9. Review Prompts ×7
10. Work Journal Handoff Prompt
