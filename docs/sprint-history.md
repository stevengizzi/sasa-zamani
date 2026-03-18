# Sprint History

> Complete record of all sprints, sessions, and outcomes.

| Sprint | Name | Tests | Date | Key DECs |
|--------|------|-------|------|----------|
| 1 | Backend Foundation + Data Pipeline | 0 → 93 (90 pass, 3 skip) | 2026-03-18 | DEC-012, DEC-013 |

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
