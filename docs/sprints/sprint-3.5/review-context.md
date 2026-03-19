# Sprint 3.5 — Review Context

> This file is referenced by all session review prompts. It contains the Sprint Spec,
> Specification by Contradiction, Regression Checklist, and Escalation Criteria.

---

## Sprint Spec

### Goal
Replace speaker-turn splitting with Claude-powered thematic segmentation for all transcript ingestion (batch seeding and live Granola upload). Generate meaningful LLM labels for all event types. Add multi-participant attribution to the events schema. Re-seed production with improved data quality before Edge City demo.

### Deliverables
1. `participants` jsonb column on events table with full stack integration
2. Thematic segmentation engine (`app/segmentation.py`)
3. Updated Granola pipeline using thematic segmentation
4. Updated batch seeding script using thematic segmentation
5. Telegram label generation (Claude-generated 3-5 word summaries)
6. Production re-seed with thematically segmented data

### Key Decisions
- DEC-017: Multi-participant events: `participant = "shared"` + `participants` jsonb array
- DEC-018: Thematic segmentation for both batch seeding and live Granola upload
- DEC-019: Combined segmentation + label call (one Claude call per transcript)
- Telegram label failure falls back to `text[:80]`
- Segmentation failure fails the upload (no silent fallback)
- Zero-speaker segments: `participant = "shared"`, `participants: []`

### Session Breakdown
| Session | Scope | Creates | Modifies |
|---------|-------|---------|----------|
| S1a | Segmentation engine | `segmentation.py`, `test_segmentation.py` | — |
| S1b | Schema integration | — | `db.py`, `models.py`, `init_supabase.sql`, `test_db.py` |
| S2a | Granola + seed pipeline | — | `granola.py`, `seed_transcript.py`, `test_granola.py`, `test_seed_transcript.py` |
| S2b | Telegram labels | — | `telegram.py`, `test_telegram.py` |
| S3 | Re-seed + verify | `backfill_labels.py` | — |

Dependency: S1a → S1b → S2a → S2b → S3

---

## Specification by Contradiction

### Out of Scope
- Dynamic clustering / centroid recomputation
- Myth post-validation (DEF-017)
- Transcript dedup (DEF-018)
- Frontend changes for `participants` display
- Frontend changes of any kind
- Myth regeneration trigger (automatic via existing `should_regenerate`)
- Telegram message segmentation (only labels)

### Files That Must NOT Be Modified
- `app/config.py`
- `app/embedding.py`
- `app/myth.py`
- `app/clustering.py`
- `app/main.py`
- `static/index.html`
- `tests/conftest.py`
- `tests/test_myth.py`
- `tests/test_clustering.py`
- `tests/test_endpoints.py`

### Interaction Boundaries
- `/clusters` endpoint behavior unchanged
- `/myth` endpoint behavior unchanged
- Myth generation pipeline untouched
- Clustering assignment logic (`assign_cluster`) untouched
- XS computation untouched
- Frontend rendering unchanged

---

## Regression Checklist

### Test Suite Baseline
- Pre-sprint: 147 passed, 3 skipped, 3 pre-existing errors (FK teardown)
- Hard floor: ≥118 pass

### Critical Invariants
| # | Invariant | How to Verify |
|---|-----------|---------------|
| 1 | `insert_event()` backward compatible | Existing test_db tests pass without `participants` arg |
| 2 | `/events` endpoint returns valid data | Existing test_endpoints tests pass |
| 3 | `/clusters` endpoint returns valid data | Existing test_endpoints tests pass |
| 4 | Myth generation pipeline untouched | Existing test_myth tests pass; `app/myth.py` not modified |
| 5 | Clustering assignment logic untouched | Existing test_clustering tests pass |
| 6 | Frontend renders both views | Visual check (no `static/index.html` changes) |
| 7 | Telegram pipeline inserts events | test_telegram tests pass |
| 8 | Granola pipeline processes uploads | test_granola tests pass |
| 9 | `seed_transcript.py` dry-run works | test_seed_transcript confirms dry-run |
| 10 | XS computation still works | Existing xs tests pass |

---

## Escalation Criteria

1. Segmentation output ratio anomaly: < 50% or > 150% of speaker-turn count
2. Claude API cost per transcript exceeds $0.50
3. Segmentation produces semantically incoherent segments on manual review
4. Test pass count drops below 118
5. `insert_event()` backward compatibility broken
6. Schema change requires migration beyond single ALTER TABLE
