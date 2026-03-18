# Sprint 1: Review Context

> This file is read by every Tier 2 review session. It contains the Sprint Spec,
> Specification by Contradiction, Regression Checklist, and Escalation Criteria.
> Individual session review prompts reference this file by path.

---

## Sprint Spec

### Goal
Stand up the full backend data pipeline for Sasa/Zamani — from receiving input (Telegram messages, Granola transcripts) through OpenAI embedding and cluster assignment to serving events and clusters via REST API on Railway. This sprint creates the entire server-side foundation that Sprint 2's frontend migration will consume.

### Deliverables
1. FastAPI application deployed on Railway with health endpoint reporting DB connection status
2. Supabase schema with events table (pgvector embeddings) and clusters table
3. Pydantic models for request/response validation
4. GET /events endpoint with optional ?participant= filter
5. GET /clusters endpoint returning six seed clusters with archetype names and event counts
6. OpenAI embedding pipeline — embed_text() producing 1536-dim vectors
7. Cluster assignment logic — cosine similarity, nearest-cluster assignment
8. Six seed cluster centroids computed from representative text
9. POST /telegram endpoint — full embed → assign → store pipeline
10. POST /granola endpoint — parse, embed, assign, store
11. End-to-end integration tests

### Acceptance Criteria

**FastAPI on Railway:**
- GET /health returns 200 with {"status": "healthy", "database": "connected"}
- App starts without error with all required env vars
- App fails fast with clear error if required env vars missing

**Supabase schema:**
- events table: id (UUID), label (text), note (text), participant (text), embedding (vector(1536)), cluster_id (UUID FK), created_at (timestamptz), source (text)
- clusters table: id (UUID), name (text), centroid_embedding (vector(1536)), event_count (int), last_updated (timestamptz)
- pgvector extension enabled, cosine similarity operator (<=>) works

**GET /events:**
- Returns JSON array (empty array when no events)
- Excludes raw embedding vectors
- ?participant= filter is case-insensitive
- Unknown participant returns empty array, not error

**GET /clusters:**
- Returns exactly 6 seed clusters
- Each includes: id, name, event_count
- Excludes centroid embeddings

**Embedding pipeline:**
- embed_text("any string") returns list of 1536 floats
- OpenAI API errors raise typed EmbeddingError
- Handles empty string without crash

**Cluster assignment:**
- Assigns to cluster with highest cosine similarity
- Deterministic (same embedding → same cluster)
- Low-confidence assignments logged but still assigned

**Seed clusters:**
- All six present: The Gate, What the Body Keeps, The Table, The Silence, The Root, The Hand
- Each has non-null centroid_embedding (1536 floats, not zero vector)
- Centroids computed from representative text

**POST /telegram:**
- Valid text message → event stored with embedding and cluster_id
- Empty message → 200, no event, warning logged
- Duplicate update_id → 200, no duplicate (idempotent)
- OpenAI failure → 503, no event stored
- Non-text message → 200, logged as unsupported, no event

**POST /granola:**
- Speaker-labeled transcript → events attributed to correct participants
- No speaker labels → single event, participant = "shared"
- Empty transcript → 400 with error message
- Each segment independently embedded and cluster-assigned

**Integration:**
- POST /telegram → GET /events shows new event with correct cluster
- POST /granola → GET /events shows parsed events with correct participants
- GET /clusters event_count reflects actual assigned events

### Performance Benchmarks
| Metric | Target |
|--------|--------|
| Embedding generation | < 2s per event |
| GET /events (empty) | < 200ms |
| GET /events (100 events) | < 500ms |
| POST /telegram end-to-end | < 5s |

### Config
Env vars via Pydantic Settings: SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, TELEGRAM_BOT_TOKEN (all required), CLUSTER_JOIN_THRESHOLD (default 0.3).

---

## Specification by Contradiction

### Out of Scope
- POST /myth endpoint (deferred to Sprint 2)
- Frontend changes (static/index.html untouched)
- Dynamic cluster creation (only 6 seed archetypes)
- Authentication or authorization
- Real-time updates (WebSocket/SSE)
- Event deletion or editing
- Telegram media attachments (text only)
- HNSW index optimization
- Rate limiting
- Decay mechanics, truth candidates, myth narrative (Layers 3-4)

### Edge Cases to Reject
- Telegram media → log unsupported, return 200, no event
- Telegram group/channel messages → log and skip
- Events with identical text → store as separate events
- Cluster centroid drift → do NOT recompute centroids

### Scope Boundaries
- Do NOT modify: static/index.html, any docs/ files
- Do NOT optimize: embedding storage, cluster assignment (brute-force over 6 centroids)
- Do NOT add: logging infra beyond stdlib, CI/CD, Docker config

### Deferred Items
| Item | DEF |
|------|-----|
| POST /myth | DEF-001 |
| Frontend migration | DEF-002 |
| Dynamic clusters | DEF-003 |
| Centroid recomputation | DEF-004 |
| Event decay | DEF-005 |
| Auth / participant mgmt | DEF-006 |
| HNSW index | DEF-007 |
| Telegram media | DEF-008 |
| Telegram groups | DEF-009 |

---

## Regression Checklist

| # | Invariant | How to Verify |
|---|-----------|---------------|
| 1 | Health endpoint returns 200 | curl /health returns 200 with JSON body |
| 2 | Health endpoint reports DB status | GET /health includes "database" field |
| 3 | GET /events returns valid JSON array on empty DB | curl /events returns [] |
| 4 | GET /events excludes embedding vectors | Response has no "embedding" field |
| 5 | GET /clusters returns exactly 6 seed clusters | curl /clusters returns array length 6 |
| 6 | GET /clusters excludes centroid embeddings | Response has no "centroid_embedding" field |
| 7 | No partial writes on embedding failure | Simulate OpenAI failure; events table unchanged |
| 8 | Telegram webhook always returns 200 | Malformed payload → 200 response |
| 9 | Duplicate update_id → no duplicate event | Same update_id twice → single event |
| 10 | Cluster assignment is deterministic | Same text embedded twice → same cluster |
| 11 | Seed centroids are non-null, non-zero, 1536-dim | Query clusters table directly |
| 12 | App starts cleanly with all env vars | uvicorn exits 0 |
| 13 | App fails fast on missing env vars | Remove SUPABASE_URL → startup error |
| 14 | Participant filter is case-insensitive | ?participant=Jessie and ?participant=jessie match |

---

## Escalation Criteria

1. Supabase pgvector unavailable → STOP
2. Railway deployment fails 3+ consecutive times → STOP
3. OpenAI embedding dimensions ≠ 1536 → STOP
4. Degenerate cluster assignment (>80% to one cluster) → STOP (RSK-001)
5. Cosine similarity uniformly > 0.95 or < 0.1 → STOP
6. Any session exceeds 2× estimated test count → STOP
7. supabase-py requires >20 lines raw SQL for vector ops → document + escalate
8. Telegram webhook needs different endpoint structure → document + escalate
9. Compaction in Session 4b → partial close-out + follow-up session
