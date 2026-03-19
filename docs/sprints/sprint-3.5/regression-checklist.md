# Sprint 3.5 — Regression Checklist

## Test Suite Baseline
- Pre-sprint: 147 passed, 3 skipped, 3 pre-existing errors (FK teardown)
- Hard floor: ≥118 pass

## Critical Invariants

| # | Invariant | How to Verify |
|---|-----------|---------------|
| 1 | `insert_event()` backward compatible | Existing test_db tests pass without `participants` arg |
| 2 | `/events` endpoint returns valid data | Existing test_endpoints tests pass |
| 3 | `/clusters` endpoint returns valid data | Existing test_endpoints tests pass |
| 4 | Myth generation pipeline untouched | Existing test_myth tests pass; `app/myth.py` not modified |
| 5 | Clustering assignment logic untouched | Existing test_clustering tests pass; `app/clustering.py` not modified |
| 6 | Frontend renders both views | Visual check on production (no `static/index.html` changes) |
| 7 | Telegram pipeline inserts events | Existing test_telegram tests pass + new label tests |
| 8 | Granola pipeline processes uploads | Updated test_granola tests pass with segmentation |
| 9 | `seed_transcript.py` dry-run works | Updated test confirms dry-run calls segmentation but not DB |
| 10 | XS computation still works | Existing xs tests pass; `app/clustering.py` not modified |

## Files That Must NOT Be Modified

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
