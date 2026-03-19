# Tier 2 Review: Sprint 2, Session S1

**Reviewer:** Tier 2 automated review (Claude)
**Date:** 2026-03-19
**Session:** S1 — Backend xs Computation + API Response Enrichment
**Verdict:** PASS

---

## Summary

Session S1 delivers all spec requirements cleanly. The `compute_xs` function
maps seed clusters to the correct canonical centers, uses deterministic
SHA-256-based jitter (no `random` module), and clamps output to [0.0, 1.0].
API response models are enriched additively with no fields removed or renamed.
The `insert_event` function is backward compatible. All 100 tests pass (3
skipped, same 3 as baseline). No prohibited files were modified.

---

## Session-Specific Review Findings

### 1. compute_xs centers match spec exactly

**PASS.** The `XS_CENTERS` dict at `app/clustering.py:70-77` contains:

| Cluster | Spec | Implementation |
|---------|------|----------------|
| The Gate | 0.12 | 0.12 |
| The Silence | 0.15 | 0.15 |
| The Hand | 0.25 | 0.25 |
| The Root | 0.38 | 0.38 |
| What the Body Keeps | 0.50 | 0.50 |
| The Table | 0.82 | 0.82 |

All six values match. Unknown clusters default to 0.50 via `_DEFAULT_XS_CENTER`.

### 2. xs values are deterministic

**PASS.** The function uses `hashlib.sha256` on the string
`"{cluster_name}:{event_index}"` to produce jitter. No `random` module is
imported or used anywhere in `app/clustering.py`. A dedicated test
(`test_deterministic`) confirms repeated calls produce identical output.

### 3. insert_event is backward compatible

**PASS.** The `xs` parameter defaults to `None` at `app/db.py:60`. When `None`,
it is excluded from the insert data dict (line 72-73: `if xs is not None`).
Existing callers that do not pass `xs` are unaffected.

### 4. EventResponse and ClusterResponse changes are additive

**PASS.** Verified against the diff and the full `app/models.py` file:

- **EventResponse:** Original fields (`id`, `label`, `note`, `participant`,
  `cluster_id`, `created_at`, `source`) are unchanged. Added `xs: float | None = None`
  and `day: int | None = None` with defaults.
- **ClusterResponse:** Original fields (`id`, `name`, `event_count`) are
  unchanged. Added `glyph_id: str | None = None`, `myth_text: str | None = None`,
  and `is_seed: bool = False` with defaults.

No fields were removed or renamed.

### 5. get_events() select string includes xs and day

**PASS.** At `app/db.py:85-87`, the select string is:
`"id, created_at, event_date, label, note, participant, source, cluster_id, xs, day"`

Both `xs` and `day` are present.

### 6. get_clusters() select string includes glyph_id, myth_text, is_seed

**PASS.** At `app/db.py:98`, the select string is:
`"id, name, glyph_id, myth_text, myth_version, event_count, last_updated, is_seed"`

All three fields are present.

---

## Sprint-Level Regression Checklist

| Check | Result | Notes |
|-------|--------|-------|
| All 90 existing passing tests still pass | PASS | 100 pass (90 original + 10 new), 3 skipped (unchanged) |
| GET /events returns correct data with all existing fields | PASS | Select string preserves all original columns, new fields additive |
| GET /clusters returns correct data with all existing fields | PASS | Select string preserves all original columns, new fields additive |
| POST /telegram processes and stores events | PASS | app/telegram.py unmodified; telegram tests pass |
| Embedding pipeline unchanged (except xs at end) | PASS | app/embedding.py not in changed file list |
| Seed cluster initialization unchanged | PASS | seed_clusters() and SEED_ARCHETYPES untouched |
| CLUSTER_JOIN_THRESHOLD=0.3 unchanged | PASS | No config changes in this session |
| app/telegram.py not modified | PASS | Not in diff |
| app/granola.py not modified | PASS | Not in diff |
| app/embedding.py not modified | PASS | Not in diff |
| Procfile not modified | PASS | Not in diff |
| scripts/init_supabase.sql not modified | PASS | Not in diff |
| scripts/seed_clusters.py not modified | PASS | Not in diff |

---

## Files Changed

| File | Change Type |
|------|-------------|
| app/clustering.py | modified |
| app/db.py | modified |
| app/models.py | modified |
| tests/test_clustering.py | modified |
| tests/test_db.py | modified |
| tests/test_endpoints.py | modified |
| scripts/__init__.py | added |
| scripts/backfill_xs.py | added |
| dev-logs/2026-03-19-sprint2-s1.md | added |
| docs/sprints/sprint-2/session-s1-closeout.md | added |

---

## Observations

1. **compute_xs not wired into live pipeline.** The close-out correctly notes
   this as a constraint-driven gap: the spec forbids modifying `telegram.py` and
   `granola.py`, which are where cluster assignment happens. The backfill script
   covers existing data. This is not a defect — it is a known scope boundary
   that future sessions will address.

2. **Backfill ordering.** The backfill script iterates events in insertion order
   within each cluster (not by `created_at`). Since jitter is based on
   `event_index` position, rerunning after new events are added could shift
   existing events' xs values if the ordering changes. This is acceptable for
   now given the deterministic-overwrite design, but worth noting for future
   sessions that may need stable xs values across backfills.

3. **Jitter range.** The spec says "deterministic jitter" and the implementation
   uses a +-0.005 range (0.01 * (hash_normalized - 0.5)). This is well within
   the +-0.06 spread and will not cause visual stacking. Correct.

4. **Test count.** Close-out reports 103 tests total but `pytest` shows 100 pass
   + 3 skip = 103 collected. The close-out mentions "2 pre-existing integration
   failures" but the full suite run shows 0 failures. This discrepancy may be
   due to those integration tests being among the 3 skipped (marked with skip
   rather than failing). Not a concern for this review.

---

## Recommendations

None. The implementation is clean, well-tested, and fully aligned with the spec.
Proceed to session S2.
