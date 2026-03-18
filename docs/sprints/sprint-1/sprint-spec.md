# Sprint 1: Backend Foundation + Data Pipeline

## Goal
Stand up the full backend data pipeline for Sasa/Zamani — from receiving input (Telegram messages, Granola transcripts) through OpenAI embedding and cluster assignment to serving events and clusters via REST API on Railway. This sprint creates the entire server-side foundation that Sprint 2's frontend migration will consume.

## Scope

### Deliverables
1. **FastAPI application deployed on Railway** with health endpoint reporting DB connection status
2. **Supabase schema** with events table (pgvector embeddings) and clusters table, accessed via a Python DB client module
3. **Pydantic models** for request/response validation across all endpoints
4. **GET /events endpoint** returning all events as JSON with optional `?participant=` filter
5. **GET /clusters endpoint** returning six seed cluster definitions with archetype names and event counts
6. **OpenAI embedding pipeline** — `embed_text()` function producing 1536-dim vectors via text-embedding-3-small
7. **Cluster assignment logic** — cosine similarity against cluster centroids, nearest-cluster assignment
8. **Six seed cluster centroids** computed from representative text and stored in the clusters table
9. **POST /telegram endpoint** — Telegram webhook receiver that validates, extracts text + participant, embeds, assigns cluster, and stores
10. **POST /granola endpoint** — Granola transcript upload that parses speaker-attributed segments, embeds each, assigns clusters, and stores
11. **End-to-end integration tests** covering the full input → embed → assign → store → retrieve pipeline

### Acceptance Criteria

1. **FastAPI on Railway:**
   - `GET /health` returns 200 with `{"status": "healthy", "database": "connected"}`
   - App starts without error when all required env vars are set
   - App fails fast with clear error message if required env vars are missing

2. **Supabase schema:**
   - `events` table exists with columns: id (UUID), label (text), note (text), participant (text), embedding (vector(1536)), cluster_id (UUID FK), created_at (timestamptz), source (text)
   - `clusters` table exists with columns: id (UUID), name (text), centroid_embedding (vector(1536)), event_count (int), last_updated (timestamptz)
   - pgvector extension is enabled and cosine similarity operator (`<=>`) works

3. **GET /events:**
   - Returns JSON array (empty array when no events, not error)
   - Each event includes: id, label, note, participant, cluster_id, created_at, source
   - Does NOT return raw embedding vectors (too large for API response)
   - `?participant=jessie` returns only events where participant = "jessie" (case-insensitive)
   - `?participant=nonexistent` returns empty array, not error

4. **GET /clusters:**
   - Returns JSON array with exactly 6 seed clusters
   - Each cluster includes: id, name, event_count
   - Does NOT return centroid embeddings in response
   - event_count reflects actual count of assigned events

5. **Embedding pipeline:**
   - `embed_text("any string")` returns a list of 1536 floats
   - Handles OpenAI API errors gracefully (raises a typed exception, does not crash)
   - Handles empty string input (returns embedding — OpenAI handles this)

6. **Cluster assignment:**
   - Given an event embedding and 6 cluster centroids, assigns to the cluster with highest cosine similarity
   - Assignment is deterministic (same embedding always maps to same cluster)
   - Low-confidence assignments (below CLUSTER_JOIN_THRESHOLD) are still assigned but logged

7. **Seed clusters:**
   - All six archetypes present: The Gate, What the Body Keeps, The Table, The Silence, The Root, The Hand
   - Each has a non-null centroid_embedding (1536 floats, not zero vector)
   - Centroids computed from representative text via OpenAI embedding (not random vectors)

8. **POST /telegram:**
   - Valid Telegram webhook update with a text message → event stored with non-null embedding and cluster_id
   - Empty message body → 200 response, no event stored, warning logged
   - Duplicate update_id → 200 response, no duplicate event stored (idempotent)
   - OpenAI API failure → 503 response, no event stored (no partial writes)

9. **POST /granola:**
   - Transcript with speaker labels → multiple events, each attributed to correct participant
   - Transcript without speaker labels → single event attributed to "shared"
   - Empty transcript → 400 response with clear error message
   - Each parsed segment is independently embedded and cluster-assigned

10. **Integration tests:**
    - Full pipeline test: create event via POST /telegram → verify in GET /events → verify cluster assignment in GET /clusters (event_count incremented)
    - Granola pipeline test: upload transcript → verify parsed events appear in GET /events with correct participant attribution

### Performance Benchmarks
| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Embedding generation | < 2s per event | Timed OpenAI API call in integration test |
| GET /events (empty) | < 200ms | Response time in test |
| GET /events (100 events) | < 500ms | Response time with seeded test data |
| POST /telegram end-to-end | < 5s | Timed from request to stored event |

### Config Changes
Environment variables via Pydantic Settings (no YAML config files):

| Env Var | Pydantic Field | Default |
|---------|---------------|---------|
| SUPABASE_URL | supabase_url | (required) |
| SUPABASE_KEY | supabase_key | (required) |
| OPENAI_API_KEY | openai_api_key | (required) |
| TELEGRAM_BOT_TOKEN | telegram_bot_token | (required) |
| CLUSTER_JOIN_THRESHOLD | cluster_join_threshold | 0.3 |

## Dependencies
- Supabase project created with pgvector extension enabled
- Railway app created and linked to GitHub repo (https://github.com/stevengizzi/sasa-zamani.git)
- Telegram bot created via BotFather (bot token available)
- OpenAI API key with access to text-embedding-3-small
- Python 3.12 runtime on Railway

## Relevant Decisions
- DEC-001: Python + FastAPI — constrains language and framework choice
- DEC-002: Supabase + pgvector — constrains database and vector storage approach
- DEC-003: OpenAI text-embedding-3-small — constrains embedding dimension (1536) and API dependency
- DEC-004: Railway deployment — constrains hosting and deploy mechanism
- DEC-006: Telegram + Granola — constrains input modalities for this sprint
- DEC-011: Seed clusters, dynamic deferred — only 6 fixed archetypes, no cluster creation logic

## Relevant Risks
- RSK-001: Embedding quality insufficient for meaningful clustering — this sprint is the first real test. Seed cluster centroids computed from representative text may not produce intuitive assignments. Mitigation: log all assignments with similarity scores for manual review.
- RSK-007: Philosophical coherence under implementation pressure — the seed archetype names and representative text must be chosen carefully. The Gate, The Silence, etc. are not arbitrary labels.

## Session Count Estimate
7 sessions. The repo has a bootstrapped scaffold (stub files, dependencies, SQL scripts) but no implemented logic. Sessions split to keep compaction risk manageable: scaffold + config (1), database (2a, 2b), embedding/clustering (3a, 3b), input handlers (4a, 4b). Strict sequential dependency chain.
