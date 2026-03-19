# Sprint History

> Complete record of all sprints, sessions, and outcomes.

| Sprint | Name | Tests | Date | Key DECs |
|--------|------|-------|------|----------|
| 1 | Backend Foundation + Data Pipeline | 0 → 93 (90 pass, 3 skip) | 2026-03-18 | DEC-012, DEC-013 |
| 2 | Frontend Migration | 93 → 123 (118–119 pass, 2–3 skip) | 2026-03-19 | DEC-014 |

---

## Sprint 1 — Backend Foundation + Data Pipeline

**Goal:** Stand up the full backend data pipeline — Telegram/Granola input → OpenAI embedding → cluster assignment → Supabase storage → REST API serving.

**Sessions:** S1, S2a, S2b, S3a, S3b, S3b-completion, S4a, S4b, S4c (9 sessions)

**Test delta:** 0 → 93 (90 pass, 3 skip)

**Key outcomes:**
- FastAPI backend deployed on Railway with health check, events, clusters, telegram, granola, and myth endpoints
- Supabase schema with pgvector for events, clusters, and myths tables
- OpenAI embedding pipeline with cosine similarity cluster assignment (CLUSTER_JOIN_THRESHOLD=0.3)
- Telegram webhook handler using raw JSON parsing (DEC-012) with in-memory dedup (DEC-013)
- Granola transcript parser with speaker attribution
- Seed cluster centroids validated: 6/6 cluster sanity test, centroid similarity matrix healthy (spread 0.25–0.49, mean 0.33)
- RSK-001 (embedding quality) downgraded from High to Low
- New files: app/config.py, pyproject.toml, scripts/centroid_matrix.py, scripts/cluster_sanity.py, full test suite (9 test files)

**Carry-forwards:**
- DEF-010: increment_event_count not atomic
- DEF-011: SEED_ARCHETYPES duplicated between app/ and scripts/
- DEF-012: Non-atomic insert + increment
- DEF-013: In-memory dedup set grows unbounded
- DEF-014: process_granola_upload returns cluster_id as cluster_name

**Review verdicts:** S1 PASS, S2a PASS, S2b APPROVED, S3a PASS, S3b PASS_WITH_NOTES, S4a PASS_WITH_NOTES, S4b PASS, S4c PASS

---

## Sprint 2 — Frontend Migration

**Goal:** Migrate the Sasa Map frontend from hardcoded mock data to live backend API data. Complete the myth generation pipeline. Add participant colors and individual/collective toggle.

**Sessions:** S1, S3a, S3b, S2, S2f, S2f2, Pipeline Fix, S3c, S4 (9 sessions; S3cf and S4f skipped — no blocking issues)

**Test delta:** 93 → 123 (+30 new tests)

**Key outcomes:**
- Frontend migrated from hardcoded data to async API fetches (`/events`, `/clusters`)
- Myth generation module implemented (`app/myth.py`): `build_myth_prompt`, `should_regenerate`, `generate_myth`, `get_or_generate_myth` with PROHIBITED_WORDS enforcement
- `/myth` POST endpoint wired with `MythRequest`/`MythResponse` models
- `compute_xs` pipeline wired into both `telegram.py` and `granola.py` (DEC-014: constraint lifted mid-sprint)
- `increment_event_count` verified in live pipeline
- Participant color encoding (Jessie purple, Emma coral, Steven teal, shared gold) with individual/collective toggle
- Opacity fade for non-selected participants in collective mode
- Chained panel navigation fix (stopPropagation)
- Div-by-zero fix in edge weight calculation (event_count=0 guard)
- New DB functions: `get_cluster_by_id`, `get_cluster_events_labels`, `get_latest_myth`, `insert_myth`, `update_cluster_myth`
- New files: `scripts/__init__.py`, `scripts/backfill_xs.py`, `tests/test_myth.py`

**Issues resolved during sprint:**
- PROHIBITED_WORDS missing "unlock" and "activate" → added in S3b
- Redundant delta test (both delta=3) → fixed in S3b
- compute_xs not wired into live pipeline → wired in Pipeline Fix session
- glyph_id null on seed clusters → manual SQL fix applied
- Toggle dead after panel open (div-by-zero in edge weight) → fixed in S2f2
- Chained panel navigation closing instead of transitioning → stopPropagation fix in S2f
- event_count always 0 → confirmed already wired; Pipeline Fix verified

**Carry-forwards:**
- DEF-010: Non-atomic increment_event_count (pre-existing from Sprint 1, confirmed still open)
- DEF-016: seed_clusters.py does not populate glyph_id column (manual DB fix applied; script fix needed)

**Scope changes:**
- DEC-014: Lifted do-not-modify constraint on telegram.py/granola.py for pipeline wiring fix
- S2f and S2f2 were unplanned fix sessions for panel/toggle interaction bugs
- Pipeline Fix was an unplanned session to wire compute_xs and verify event_count

**Review verdicts:** S1 PASS, S3a CLEAR, S3b APPROVED_WITH_CONCERNS, S2 APPROVED, S2f PASS, S2f2 PASS, Pipeline Fix PASS, S3c APPROVED, S4 CLEAR
