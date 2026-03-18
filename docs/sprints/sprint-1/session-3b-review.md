# Tier 2 Review: Sprint 1 — Session 3b (Cluster Assignment + Seed Clusters)

**Reviewer:** @reviewer (Claude)
**Date:** 2026-03-18
**Verdict:** PASS_WITH_NOTES

---

## Review Focus Checklist

| # | Focus Item | Verdict | Notes |
|---|-----------|---------|-------|
| 1 | SEED_ARCHETYPES has exactly 6 entries matching spec names | PASS | 6 entries with names: The Gate, What the Body Keeps, The Table, The Silence, The Root, The Hand. Tests assert both count and exact name set. |
| 2 | cosine_similarity is a pure math function (no external deps) | PASS | Uses only `math.sqrt`, `sum`, and `zip`. No imports of embedding, db, or any external library. Input validation via TypeError/ValueError per CLAUDE.md standard #8. |
| 3 | assign_cluster returns nearest cluster even below threshold (logs, doesn't error) | PASS | Below-threshold path issues `logger.warning` and still returns `(best_id, best_score)`. Test `test_below_threshold_logs_warning` confirms: orthogonal vectors yield score 0.0, cluster is still returned, and "below threshold" appears in log output. |
| 4 | seed_clusters is idempotent (cluster_exists guard) | PASS | `seed_clusters()` calls `cluster_exists(name)` before each insertion and skips with `logger.info` if the cluster already exists. Guard is per-cluster, not all-or-nothing, which is correct. |
| 5 | Centroid similarity matrix in close-out | NOTE | **Not computed.** Close-out acknowledges this and defers to the first integration run with a real OpenAI API key. Escalation criteria #4 (degenerate assignment) and #5 (uniform similarity) cannot be evaluated until then. This is a known gap, not a failure — the mocked tests verify the pipeline structure correctly. |
| 6 | Representative text matches spec exactly (no modifications) | PASS | Character-for-character comparison between `app/clustering.py` SEED_ARCHETYPES and `scripts/seed_clusters.py` SEED_ARCHETYPES confirms all six entries are identical: names, glyph_ids, tags, and representative_text strings all match. |
| 7 | clustering.py imports embedding.py (not the reverse) | PASS | `app/clustering.py` line 7: `from app.embedding import embed_texts`. Grep of `app/embedding.py` for any clustering import returned zero matches. Dependency flows one way as required. |

## Forbidden File Check

| File | Modified? | Verdict |
|------|-----------|---------|
| `static/index.html` | No | PASS |
| `app/embedding.py` | No | PASS |
| `app/main.py` | No | PASS |
| `docs/` (non-sprint) | No | PASS |

Files changed in this commit: `app/clustering.py` (modified), `app/db.py` (modified), `tests/test_clustering.py` (added), `docs/sprints/sprint-1/session-3b-closeout.md` (added). All within scope.

## Test Results

```
17 passed, 1 warning in 0.32s  (tests/test_clustering.py)
47 passed, 3 skipped, 2 warnings in 0.55s  (full suite)
```

- 14 unit tests passed for clustering module
- 3 integration test stubs passed (empty bodies, marked `@pytest.mark.integration`)
- 3 skipped tests are pre-existing embedding integration tests (no real API key)
- 0 failures
- Full suite regression: all 47 tests pass

## Observations

1. **Unused `db_client` parameter on `seed_clusters`:** The function signature accepts `db_client` but never uses it — it imports `cluster_exists` and `insert_cluster` directly via lazy imports. The close-out acknowledges this as a future cleanup item. Not a blocker, but it is a misleading API surface. A future session should either wire `db_client` through or remove the parameter.

2. **Lazy imports in `seed_clusters`:** The `from app.db import cluster_exists, insert_cluster` at function scope (line 133) avoids a circular import. This is a reasonable trade-off. The close-out documents the rationale.

3. **Integration test stubs:** Three integration tests have `pass` bodies. These are placeholders gated on a real Supabase connection. Acceptable for this session since the unit tests cover the logic thoroughly.

4. **pytest.mark.integration not registered:** The test run emits `PytestUnknownMarkWarning` for the unregistered `integration` mark. This should be registered in `pyproject.toml` or `pytest.ini` in a future session to silence the warning.

5. **Centroid similarity matrix deferred:** This is the only substantive gap. Escalation criteria #4 and #5 remain unevaluable until real embeddings are generated. The close-out correctly flags this. Not blocking for session sign-off, but must be addressed before sprint close-out.

6. **SEED_ARCHETYPES intentional duplication:** The data is duplicated between `app/clustering.py` and `scripts/seed_clusters.py`. The close-out justifies this as avoiding an app-to-scripts dependency. Reasonable — the script is a standalone runner. A single-source-of-truth refactor (e.g., shared constants module) could be considered later but is not necessary now.

## Close-out Report Accuracy

The close-out report accurately reflects the implementation. Self-assessment of MINOR_DEVIATIONS is confirmed — the only deviation is the deferred centroid similarity matrix, which is correctly documented. Test counts (47 total, 17 new) match observed results.

---

**Verdict: PASS_WITH_NOTES** — All review focus items satisfied. No forbidden files modified. Tests pass. Implementation is correct and well-structured. The single note is the deferred centroid similarity matrix, which must be computed during the first integration run with real API credentials before sprint close-out.
