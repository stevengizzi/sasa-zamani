# Sprint History

> Complete record of all sprints, sessions, and outcomes.

| Sprint | Name | Tests | Date | Key DECs |
|--------|------|-------|------|----------|
| 1 | Backend Foundation + Data Pipeline | 0 → 93 (90 pass, 3 skip) | 2026-03-18 | DEC-012, DEC-013 |
| 2 | Frontend Migration | 93 → 123 (118–119 pass, 2–3 skip) | 2026-03-19 | DEC-014 |
| 3 | Integration Testing + Edge City Demo Prep | 125 → 147 (144 pass, 3 skip) | 2026-03-19 | DEC-015, DEC-016 |
| 3.5 | Thematic Segmentation + LLM Labels | 147 → 166 (166 pass, 0 skip) | 2026-03-19 | DEC-017, DEC-018, DEC-019, DEC-020 |
| 4 | Data Quality + Significance Filtering | 166 → 237 (237 pass, 0 skip) | 2026-03-20 | DEC-021, DEC-022, DEC-023, DEC-024 |

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

---

## Sprint 3 — Integration Testing + Edge City Demo Prep

**Goal:** Populate the Sasa Map with real data from two Granola transcripts, clear backend deferred-item backlog, tune myth quality, polish frontend for Edge City demo.

**Sessions:** S1a, S1b, S2, timestamp fix, S3, S4, S5 (7 sessions)

**Test delta:** 125 → 147 (+22 new tests)

**Key outcomes:**
- Resolved 6 deferred items from Sprint 1/2: DEF-010 (atomic increment via Postgres RPC, DEC-015), DEF-011 (SEED_ARCHETYPES single source of truth), DEF-012 (increment failure wrapped in try/except), DEF-013 (OrderedDict with 10k cap and FIFO eviction), DEF-014 (contract verified, confirming comment added), DEF-016 (glyph_id param added to insert_cluster)
- Built `scripts/seed_transcript.py`: batch seeding tool with speaker remapping, min-length filtering, dry-run mode, `--date` CLI argument
- Seeded ~393 events across 6 clusters from 2 Granola transcripts (Mar 17 and Mar 18)
- Myth prompt refined (FF-005): ancestral register tuning, reduced therapy-speak output
- Frontend demo polish (FF-006): strata view uses `event_date` for time axis, loading states, empty states
- Added `event_date` column to events table, `insert_event()`, and `EventResponse` model (DEC-016)
- XS_CENTERS adjusted: Gate 0.12→0.08, Silence 0.15→0.20 (resolved overlap)
- `testpaths = ["tests"]` added to `pyproject.toml` to prevent pytest collecting `scripts/test_myth_quality.py`
- New files: `scripts/seed_transcript.py`, `tests/test_seed_transcript.py`, `scripts/test_myth_quality.py`

**Issues resolved during sprint:**
- S1a CONCERN: Postgres RPC function required → created manually in Supabase
- S1b CONCERN: Asymmetric xs protection in granola.py → fixed in post-review
- S2 CONCERN: Potential UnboundLocalError in xs try block → fixed in post-review
- S4 post-deploy: event_date missing from API response → DEC-016, models.py fix

**Carry-forwards:**
- DEF-017: Myth post-validation (verify generated myths pass PROHIBITED_WORDS and register checks)
- DEF-018: Transcript dedup (prevent re-seeding same transcript)
- DEF-019: Event labels use raw text[:80] instead of LLM-generated summary

**Scope changes:**
- Timestamp fix (between S2 and S3): Added `--date` CLI arg and `event_date` param to `insert_event()` — unplanned but necessary
- S4 scope addition: Strata view uses `event_date` for time axis (discovered all seeded events piled at March 19)
- DEC-016: Lifted do-not-modify constraint on `app/models.py` for one-line `event_date` addition
- S3 scope addition: `testpaths = ["tests"]` in `pyproject.toml`

**Observations:**
- March 18 transcript produces 129 "shared" participant events (60% of that transcript)
- Seed cluster centroids computed from tags, not embedding model — most events assigned below 0.3 cosine similarity threshold. Centroid recomputation deferred.
- Integration test teardown FK constraint errors (3 errors in TestSeedClustersIntegration) — pre-existing, not Sprint 3 scope

**Review verdicts:** S1a CONCERNS (resolved), S1b CONCERNS (resolved), S2 CONCERNS (resolved), S3 PASS, S4 CLEAR

---

## Sprint 3.5 — Thematic Segmentation + LLM Labels

**Goal:** Replace speaker-turn splitting with Claude-powered thematic segmentation for transcript ingestion (both batch and live). Generate LLM labels for all event types. Add `participants` jsonb array. Re-seed production with improved data.

**Sessions:** S1a, S1b, S2a, S2b, S3, F1, F2 (7 sessions)

**Test delta:** 147 → 166 (+19 new tests)

**Key outcomes:**
- Built `app/segmentation.py`: thematic segmentation engine with `Segment` dataclass, `segment_transcript()` (boundary-based prompt with line-numbered transcript), `generate_event_label()` (standalone for Telegram), model claude-sonnet-4-20250514
- Boundary-based segmentation prompt (DEC-020): Claude returns start_line/end_line instead of verbatim text, Python slices original transcript — reduced output to ~1-2% of input size
- Combined segmentation + label generation in single Claude call per transcript (DEC-019)
- Added `participants JSONB DEFAULT '[]'` column to events table (DEC-017): multi-speaker segments use `participant="shared"` + `participants` array
- Both `scripts/seed_transcript.py` and `app/granola.py` now call `segment_transcript()` — regex speaker-turn splitting removed (DEC-018)
- Telegram messages get LLM-generated labels via `generate_event_label()` — resolves DEF-019
- Re-seeded production: 48 events (46 granola, 2 telegram) across 6 clusters
- Built `scripts/backfill_labels.py` for retroactive label generation
- New files: `app/segmentation.py`, `scripts/backfill_labels.py`, `tests/test_segmentation.py`, `tests/test_backfill_labels.py`

**Production data (post re-seed):**
- 48 total events: granola 46, telegram 2
- By participant: shared 46, steven 2
- By cluster: The Table 33, What the Body Keeps 10, The Silence 2, The Root 1, The Gate 1, The Hand 1

**Issues resolved during sprint:**
- F1: max_tokens=4096 truncated Claude response on large transcripts → raised to 32000, timeout=120.0s
- F2: Verbatim-text prompt architecturally wrong → redesigned to boundary-based (DEC-020), max_tokens back to 4096

**Carry-forwards:**
- DEF-020: Per-participant attribution for multi-speaker Granola events (currently all participant="shared")
- DEF-021: 10,243-char segment truncation — three segments hit exactly this length, pipeline limit needs investigation

**Scope changes:**
- F1 added (unplanned fix session): max_tokens 4096→32000, timeout=120.0
- F2 added (unplanned fix session): complete prompt redesign to boundary-based (DEC-020)
- S3 interrupted and restarted when Claude Code modified segmentation.py out of scope; backfill preserved, segmentation reverted, fix sessions ran, then S3 re-seed completed

**Review verdicts:** S1a PASS, S1b PASS, S2a PASS, S2b PASS, F1 PASS, F2 PASS, S3 PASS

---

## Sprint 4 — Data Quality + Significance Filtering

**Goal:** Improve data quality across both ingestion pipelines: significance filtering, raw_input storage, marginalia labels, label dedup, below-threshold archetype creation, and DEF-021 truncation fix.

**Sessions:** S1 (Segmentation Core), S2 (DB Schema + Layer), S3 (Archetype Creation Core), S3-fix (Prohibited Words), S4a (Granola Pipeline Integration), S4b (Seed Script Integration), S5 (Telegram Pipeline Integration), S6 (DEF-021 Fix + Re-seed + Verification) — 8 sessions

**Test delta:** 166 → 237 (+71 new tests)

**Key outcomes:**
- Significance filtering in both pipelines: `generate_event_label()` returns `tuple[str, float]`, `filter_by_significance()` gates event creation at configurable threshold (default 0.3, DEC-021)
- `raw_inputs` table stores all incoming data with FK from events (`raw_input_id`, `start_line`, `end_line`) for traceability (DEC-022)
- Dynamic cluster creation with deferred archetype naming: "The Unnamed" placeholder until `event_count` reaches `archetype_naming_threshold` (default 3), then Claude generates name via `maybe_name_cluster()` in new `app/archetype_naming.py` module (DEC-023)
- Post-processing label dedup: `dedup_labels()` appends ordinal suffixes "(II)", "(III)" for duplicate labels within a transcript (DEC-024)
- DEF-021 truncation fix: `max_tokens` increased 4096→16384 in segmentation, `stop_reason` guard added, shared-boundary tolerance for adjacent segments
- Granola pipeline rewritten: store raw → segment → dedup → filter → embed → assign/create → insert → increment → name → xs
- Seed script pipeline updated to mirror Granola pattern; `filter_by_length` removed, replaced by significance filtering; `--min-length` CLI arg removed
- Telegram pipeline reordered: dedup → label+sig → raw_input → significance filter → embed → assign/create → insert → increment → name → xs
- Production re-seeded: 29 events across 7 clusters (6 seed + 1 dynamic "The Argot") from 2 Granola transcripts
- New files: `app/archetype_naming.py`, `tests/test_archetype_naming.py`, `scripts/migrate_sprint4.sql`
- Modified files: `app/config.py`, `app/segmentation.py`, `app/clustering.py`, `app/db.py`, `app/granola.py`, `app/telegram.py`, `scripts/seed_transcript.py`, `scripts/init_supabase.sql`, plus 6 test files

**Issues resolved during sprint:**
- S3 review: 5 prohibited words missing from archetype naming prompt → fixed in S3-fix (34890db)
- S4a review: test_seed_transcript.py import error (filter_by_length removed) → resolved by S4b
- S4a review: test_telegram.py 2 test failures (tuple mock) → resolved by S5
- DEF-021: max_tokens 4096→16384 + stop_reason guard; re-seed confirms no truncation (S6)

**Carry-forwards:**
- DEF-022: Single-event cluster node unclickable in frontend (The Root)
- DEF-023: Strata view bottom margin overlaps navigation toggles
- Seed archetype expansion needed — 28/29 re-seeded events concentrated in one dynamic cluster ("The Argot"); seed archetypes designed for personal experience, not intellectual discussion
- `backfill_labels.py` needs updating to handle tuple return from `generate_event_label()`
- Unused `call` import in `tests/test_granola.py:3` (cosmetic)
- Redundant exception clause `except (SegmentationError, Exception)` in `app/telegram.py:116` (pre-existing)
- Integration test FK teardown error in TestSeedClustersIntegration (pre-existing)

**Scope changes:**
- S6: Shared-boundary tolerance for adjacent segments (March 18 transcript triggered overlap error where Claude returned start_line == prev_end_line)

**Review verdicts:** S1 CONCERNS (resolved — false positives + by-design), S2 CLEAR, S3 CONCERNS (resolved — S3-fix applied), S4a CLEAR, S4b CLEAR, S5 CLEAR, S6 CLEAR
