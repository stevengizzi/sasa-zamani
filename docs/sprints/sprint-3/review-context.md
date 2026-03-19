# Sprint 3 — Review Context

> This file contains the shared review context for all Sprint 3 sessions.
> Individual session review prompts reference this file by path.
> Do NOT modify this file during reviews.

---

## Sprint Spec

### Sprint 3: Integration Testing + Edge City Demo Prep

**Goal:** Populate the Sasa Map with real data from two Granola transcripts, clear the accumulated backend deferred-item backlog, tune myth generation quality, and polish the frontend for the Edge City demo (~Mar 22). By sprint end, three participants can send Telegram messages and see them appear in a map already rich with seeded conversation data.

**Deliverables:**
1. Backend deferred-item cleanup — resolve DEF-010, DEF-011, DEF-012, DEF-013, DEF-014, DEF-016, and Gate/Silence xs overlap
2. Granola transcript seeding (FF-004) — seed production DB with March 17 + March 18 transcripts (~393 events)
3. Myth prompt refinement — improved `build_myth_prompt` passing Design Brief tonal test, thin-cluster handling
4. Frontend demo polish — Esc key close, archetype→event reverse chaining, smooth fade, loading state
5. Integration verification — documented end-to-end demo walkthrough

**Acceptance Criteria:**
- `insert_cluster` accepts optional `glyph_id` parameter and persists it
- `seed_clusters()` passes `glyph_id` from SEED_ARCHETYPES
- `increment_event_count` uses single SQL UPDATE (atomic)
- `scripts/seed_clusters.py` imports SEED_ARCHETYPES from `app/clustering`
- `_processed_update_ids` capped at 10,000 entries
- `process_granola_upload` returns actual cluster name in `cluster_name` field
- `XS_CENTERS` for The Gate = 0.08, The Silence = 0.20
- `scripts/seed_transcript.py` exists, handles both transcripts with correct speaker maps
- Segments < 100 characters filtered out; dry-run mode works
- Map loads with ≥50 real events post-seeding
- `build_myth_prompt` includes register guidance and embarrassment test
- Thin-cluster variant triggers at ≤2 events
- No PROHIBITED_WORDS in myth output
- Esc closes panels, reverse chaining works, fade animates, loading state shows
- All existing tests pass (≥122 pass, ≤3 skip)

**Performance Benchmarks:**
- Frontend load (with seeded data): < 5s
- `/events` response (~400 events): < 2s
- `/clusters` response: < 500ms

**Config Changes:** None.

**Session Count:** 5 development + 1 contingency + 1 verification = 7 total.

---

## Specification by Contradiction

### Out of Scope
1. Design Brief visual alignment (Sprint 4)
2. FF-002 thematic segmentation
3. New input modalities, mobile layout, dynamic clustering
4. Moon nodes, truth candidates, Layer 3/4
5. FF-001 dialogue, FF-003 notifications, FF-005 shareable cards
6. Privacy flag (DEF-015)
7. Glyph SVG rendering in frontend (glyph_id populated but not rendered)

### Edge Cases to Reject
1. Non-English transcript segments — process normally
2. Duplicate segments across transcripts — process both
3. Cluster with 0 events — myth returns "The pattern is still forming"
4. Seeding script run twice — doubles events, operator error, not a bug
5. March 18 speaker misattribution — accept as best-effort
6. Myth output with prohibited words despite instruction — accept for v1

### Scope Boundaries
- Do NOT modify: `app/config.py`, `app/models.py`, `app/embedding.py`, `scripts/init_supabase.sql`, `tests/conftest.py`
- Do NOT add: new API endpoints, new DB tables/columns, new Pydantic models, new external dependencies
- Do NOT change: endpoint response schemas

### Interaction Boundaries
- No changes to: `/events` GET, `/clusters` GET, `/telegram` POST, `/granola` POST, `/myth` POST, `/health` GET response contracts
- No changes to: Railway config, Supabase schema, Telegram bot registration

---

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Pre-sprint: ~125 collected, ~122 pass, ~3 skip
- Post-sprint target: ~146 collected, ~143 pass, ≤3 skip
- Hard floor: ≥118 pass

### Critical Invariants

**API Endpoint Contracts:**
- `GET /events` returns EventResponse list (id, created_at, event_date, label, note, participant, source, cluster_id, xs, day)
- `GET /events?participant=jessie` filters case-insensitively
- `GET /clusters` returns ClusterResponse list (id, name, glyph_id, myth_text, myth_version, event_count, last_updated, is_seed)
- `POST /telegram` always returns 200
- `POST /granola` returns `{"events": [...]}` on success
- `POST /myth` returns MythResponse (myth_text, cached)
- `GET /health` returns HealthResponse (status, database)

**Telegram Pipeline:**
- extract_message parses correctly
- is_duplicate works
- process_telegram_update returns correct status dict
- Participant mapping resolves by username → full name → first name
- Events stored with correct fields

**Granola Pipeline:**
- parse_transcript splits on speaker labels
- process_granola_upload: embed → assign → store → increment → xs
- Empty transcript → ValueError
- Embedding failure → EmbeddingError (no partial writes)

**Myth Generation:**
- build_myth_prompt returns non-empty string with cluster name and labels
- should_regenerate: True when no cache, True when delta ≥ 3, False when delta < 3
- generate_myth returns fallback on error
- get_or_generate_myth: cached when fresh, regenerates when stale
- Caching logic (version increment, insert_myth, update_cluster_myth) unchanged

**Frontend (visual verification):**
- Both views render
- Transition animates
- Event click → event panel
- Archetype click → archetype panel
- Panel close button works
- Participant toggle works
- Color encoding: jessie=purple, emma=coral, steven=teal, shared=gold

**Database Operations:**
- insert_event stores all fields
- insert_cluster stores name, centroid, is_seed (+ glyph_id after S1a)
- get_events returns rows without embedding
- get_clusters returns rows without centroid
- get_cluster_centroids returns parsed vectors
- cluster_exists works

---

## Sprint-Level Escalation Criteria

### Tier 3 Review Triggers
1. Atomic increment requires schema change (Postgres function/RPC/migration)
2. Seeding produces >500 events
3. Myth output fails tonal test after 3+ iterations
4. Frontend changes break existing interactions
5. Test pass count drops below 118

### In-Session Escalation
Escalate to Work Journal if:
- A file not in the session's "Modifies" list needs changes
- A file not in the session's "Creates" list is needed
- Test count exceeds estimate by >50%
- External service behaves unexpectedly
- A deferred item fix reveals a deeper architectural issue

### Decision Escalation
Reserve DEC-015 through DEC-017. Create new DEC if:
- Atomic increment requires choosing between implementations
- Transcript seeding approach changes
- Myth prompt architecture changes
- Any work contradicts an existing DEC
