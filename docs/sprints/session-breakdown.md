# Sprint 1: Session Breakdown

## Dependency Chain
```
Session 1 → Session 2a → Session 2b → Session 3a → Session 3b → Session 4a → Session 4b
```

All sessions are strictly sequential. No parallelizable sessions.

---

## Session 1: Project Scaffold + Configuration + Health Endpoint

**Objective:** Stand up the project structure, configuration system, and a running FastAPI app with a health endpoint. Deploy to Railway.

| Creates | Modifies | Integrates | Parallelizable |
|---------|----------|------------|----------------|
| `app/config.py`, `tests/conftest.py`, `tests/test_health.py` | `app/main.py` (add settings import, update /health), `requirements.txt` (add pydantic-settings, pytest, httpx) | N/A | false |

**Existing scaffold (verified, not recreated):** `app/__init__.py`, `app/main.py` (stub endpoints preserved), `requirements.txt` (base deps present), `.env.example`, `Procfile`, `tests/__init__.py`

**Compaction Risk:**

| Factor | Count | Points |
|--------|-------|--------|
| New files created | 3 | 6 |
| Files modified | 2 | 4 |
| Pre-flight reads | 2 (CLAUDE.md, docs/architecture.md) | 2 |
| New tests | ~5 | 2.5 |
| **Raw Total** | | **14.5** |

**Adjusted score: ~13 (Medium).** Reduced from original estimate because most scaffold files already exist. The substantive new work is `config.py`, `conftest.py`, and `test_health.py`, plus wiring settings into the existing `main.py`.

**Acceptance criteria:**
- `GET /health` returns `{"status": "healthy"}` (DB check comes in Session 2a)
- App starts with `uvicorn app.main:app`
- Missing required env vars produce clear startup error
- Railway deployment succeeds
- All tests pass

---

## Session 2a: Database Connection + Schema Creation

**Objective:** Create Supabase connection client, establish the events and clusters tables with pgvector, and implement basic CRUD operations.

| Creates | Modifies | Integrates | Parallelizable |
|---------|----------|------------|----------------|
| `app/db.py` (implements stub), `tests/test_db.py` | `app/main.py` (update /health with DB check, add startup schema call) | Session 1's config.py | false |

**Compaction Risk:**

| Factor | Count | Points |
|--------|-------|--------|
| New files created | 2 | 4 |
| Files modified | 2 | 2 |
| Pre-flight reads | 3 (app/main.py, app/config.py, docs/architecture.md) | 3 |
| New tests | ~8 | 4 |
| **Total** | | **13 (Medium)** |

**Acceptance criteria:**
- Supabase client connects successfully (health endpoint updated to report DB status)
- Events table created with pgvector column
- Clusters table created
- Basic insert/select operations work
- pgvector cosine similarity operator (`<=>`) functional
- All tests pass

---

## Session 2b: Pydantic Models + Read Endpoints

**Objective:** Define request/response models and implement GET /events (with participant filter) and GET /clusters.

| Creates | Modifies | Integrates | Parallelizable |
|---------|----------|------------|----------------|
| `app/models.py` (implements stub), `tests/test_endpoints.py` | `app/main.py` (wire GET /events and /clusters to db) | Session 2a's db.py | false |

**Compaction Risk:**

| Factor | Count | Points |
|--------|-------|--------|
| New files created | 2 | 4 |
| Files modified | 1 | 1 |
| Pre-flight reads | 3 (app/main.py, app/config.py, app/db.py) | 3 |
| New tests | ~10 | 5 |
| **Total** | | **13 (Medium)** |

**Acceptance criteria:**
- GET /events returns JSON array (empty array when no events)
- GET /events response excludes raw embedding vectors
- GET /events?participant=jessie filters correctly (case-insensitive)
- GET /clusters returns JSON array with 6 entries (once seeds exist — tested with fixture data)
- GET /clusters response excludes centroid embeddings
- Pydantic models validate all fields
- All tests pass

---

## Session 3a: Embedding Pipeline (OpenAI Integration)

**Objective:** Implement `embed_text()` function using OpenAI text-embedding-3-small, with error handling and mock-friendly architecture.

| Creates | Modifies | Integrates | Parallelizable |
|---------|----------|------------|----------------|
| `app/embedding.py` (implements stub), `tests/test_embedding.py` | (verify config.py and requirements.txt — deps already present) | Session 1's config.py | false |

**Compaction Risk:**

| Factor | Count | Points |
|--------|-------|--------|
| New files created | 2 | 4 |
| Files modified | 2 | 2 |
| Pre-flight reads | 3 (app/config.py, app/models.py, docs/architecture.md) | 3 |
| New tests | ~6 | 3 |
| External API debugging (OpenAI) | 1 | 3 |
| **Total** | | **15 (High)** |

**High score justified:** The external API penalty (+3) is inherent — embedding integration requires live API interaction during development. Tests will mock the OpenAI client for unit tests and include a small live-call integration test. Cannot be split further without creating incoherent fragments.

**Acceptance criteria:**
- `embed_text("hello world")` returns list of 1536 floats
- `embed_text("")` does not crash (handles gracefully)
- OpenAI API errors raise a typed `EmbeddingError` exception
- Unit tests pass with mocked OpenAI client
- One live integration test confirms real API returns 1536-dim vector
- All tests pass

---

## Session 3b: Cluster Assignment + Seed Clusters

**Objective:** Implement cluster assignment via cosine similarity, compute seed cluster centroids from representative text, and insert seed clusters into the database.

| Creates | Modifies | Integrates | Parallelizable |
|---------|----------|------------|----------------|
| `app/clustering.py` (implements stub), `tests/test_clustering.py` | `app/db.py` (add cluster_exists for idempotent seeding) | Session 3a's embedding.py, Session 2a's db.py | false |

**Compaction Risk:**

| Factor | Count | Points |
|--------|-------|--------|
| New files created | 2 | 4 |
| Files modified | 1 | 1 |
| Pre-flight reads | 4 (app/embedding.py, app/db.py, app/models.py, app/config.py) | 4 |
| New tests | ~8 | 4 |
| **Total** | | **13 (Medium)** |

**Acceptance criteria:**
- `assign_cluster(embedding, centroids)` returns the cluster_id with highest cosine similarity
- Assignment is deterministic
- Low-confidence assignments (below threshold) are flagged in logs but still assigned
- All six seed clusters inserted: The Gate, What the Body Keeps, The Table, The Silence, The Root, The Hand
- Each centroid is a real 1536-dim embedding (computed from representative text, not random)
- `GET /clusters` now returns 6 populated clusters
- All tests pass

**Seed cluster representative text (for centroid computation):**

| Archetype | Representative text |
|-----------|-------------------|
| The Gate | dreams, thresholds, migration, crossing over, departure, arrival, passage between worlds |
| What the Body Keeps | the body remembers, water, morning ritual, physical sensation, embodied knowing, waking |
| The Table | food, cooking together, shared meals, gathering, nourishment, communion, breaking bread |
| The Silence | silence, solitude, withdrawal, absence, what is not said, the space between words |
| The Root | memory, family, ancestry, mother tongue, language of origin, where you come from, inheritance |
| The Hand | writing, fieldwork, making by hand, the craft of inscription, putting pen to paper, manual labor |

---

## Session 4a: Telegram Webhook Handler

**Objective:** Implement the Telegram webhook receiver that validates payloads, extracts text and participant, and runs the full embed → assign → store pipeline. Wire together all prior sessions' output.

| Creates | Modifies | Integrates | Parallelizable |
|---------|----------|------------|----------------|
| `app/telegram.py` (implements stub), `tests/test_telegram.py` | `app/main.py` (wire POST /telegram stub to pipeline, add seed startup) | Sessions 2a/2b (db.py, models.py), 3a/3b (embedding.py, clustering.py) | false |

**Compaction Risk:**

| Factor | Count | Points |
|--------|-------|--------|
| New files created | 2 | 4 |
| Files modified | 1 | 1 |
| Pre-flight reads | 4 (app/main.py, app/embedding.py, app/clustering.py, app/db.py) | 4 |
| New tests | ~8 | 4 |
| Complex integration (3+ components) | 1 | 3 |
| **Total** | | **16 (High)** |

**High score justified:** This is the critical integration session — it wires together DB, embedding, and clustering into a single pipeline. The +3 integration penalty is inherent to the session's purpose. Cannot be split without separating file creation from wiring, which is counterproductive.

**Acceptance criteria:**
- Valid Telegram update with text message → event stored with non-null embedding and cluster_id
- Participant mapped from Telegram username (configurable mapping: username → participant name)
- Unknown Telegram user → participant = "unknown", warning logged
- Empty message body → 200 returned, no event stored, warning logged
- Duplicate update_id → 200 returned, no duplicate event (idempotent)
- Non-text message (photo, sticker, etc.) → 200 returned, logged as unsupported, no event stored
- OpenAI API failure → 503 returned, no event stored
- Supabase failure → 503 returned, no partial writes
- All tests pass

---

## Session 4b: Granola Parser + Integration Tests

**Objective:** Implement Granola transcript parsing with speaker attribution, the POST /granola endpoint, and end-to-end integration tests covering the full pipeline for both input modalities.

| Creates | Modifies | Integrates | Parallelizable |
|---------|----------|------------|----------------|
| `app/granola.py` (implements stub), `tests/test_granola.py`, `tests/test_integration.py` | `app/main.py` (wire POST /granola stub to pipeline) | Same pipeline as 4a (db, models, embedding, clustering) | false |

**Compaction Risk:**

| Factor | Count | Points |
|--------|-------|--------|
| New files created | 3 | 6 |
| Files modified | 1 | 1 |
| Pre-flight reads | 5 (app/main.py, app/telegram.py, app/embedding.py, app/clustering.py, app/db.py) | 5 |
| New tests | ~12 | 6 |
| Complex integration (3+ components) | 1 | 3 |
| **Total** | | **21 (Critical)** |

**Critical score acknowledged.** This session combines the Granola parser (a self-contained parsing module) with the integration test suite (which exercises the full pipeline). The integration tests are the natural capstone of the sprint. Splitting them into a separate session would create a session that only reads files and writes tests (score ~12) but would add an 8th session to an already long sprint. **Proceeding with caution** — the Granola parser itself is a straightforward text parser; the complexity is in the integration tests, which are read-heavy but don't create production code.

**Acceptance criteria:**
- Transcript with speaker labels (e.g., "Jessie: ...") → events attributed to correct participants
- Transcript without speaker labels → single event attributed to "shared"
- Multi-speaker transcript → multiple events, each independently embedded and cluster-assigned
- Empty transcript → 400 error with message
- Integration test: POST /telegram → GET /events shows new event with correct cluster
- Integration test: POST /granola → GET /events shows parsed events with correct participants
- Integration test: GET /clusters event_count reflects actual assigned events
- All tests pass

---

## Score Summary

| Session | Score | Risk Level | Notes |
|---------|-------|------------|-------|
| 1 | ~13 (adjusted) | Medium | Raw 22.5, adjusted for trivial boilerplate |
| 2a | 13 | Medium | |
| 2b | 13 | Medium | |
| 3a | 15 | High | External API penalty (+3) inherent |
| 3b | 13 | Medium | |
| 4a | 16 | High | Integration penalty (+3) inherent |
| 4b | 21 | Critical | Parser + integration tests combined; proceeding with caution |

**Total estimated tests: ~57**
