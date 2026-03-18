# Sprint 1, Session 2b — Tier 2 Review

**Reviewer:** Claude (Tier 2 automated review)
**Date:** 2026-03-18
**Verdict:** APPROVED

---

## Session-Specific Review Focus

### 1. EventResponse model does NOT include an embedding field
**PASS.** `app/models.py:EventResponse` declares exactly seven fields: `id`, `label`, `note`, `participant`, `cluster_id`, `created_at`, `source`. No `embedding` field is present. The Pydantic `response_model` declaration on the endpoint guarantees any extra keys from the DB row are stripped before serialization.

### 2. ClusterResponse model does NOT include a centroid_embedding field
**PASS.** `app/models.py:ClusterResponse` declares exactly three fields: `id`, `name`, `event_count`. Neither `centroid_embedding` nor `centroid` appears. Test `test_get_clusters_correct_structure` explicitly asserts both keys are absent from the response.

### 3. Participant filter is case-insensitive
**PASS.** The endpoint passes the raw query parameter to `db.get_events(participant)`, which uses Supabase `.ilike("participant", participant)` for case-insensitive matching. This was verified by reading `app/db.py` lines 69-76. The test `test_get_events_participant_filter_case_insensitive` confirms the value is forwarded to `get_events` as-is, correctly delegating case folding to the database layer.

### 4. GET /events with unknown participant returns [] not 404
**PASS.** Test `test_get_events_nonexistent_participant_returns_empty` mocks `get_events` returning `[]` for participant `"nonexistent"` and asserts status 200 with empty JSON array. The endpoint has no code path that raises 404.

### 5. response_model declared on all endpoints for OpenAPI documentation
**PASS.** All three session-relevant endpoints declare `response_model`:
- `GET /events` -- `response_model=list[EventResponse]`
- `GET /clusters` -- `response_model=list[ClusterResponse]`
- `GET /health` -- `response_model=HealthResponse`

### 6. db.py was not modified (only called)
**PASS.** `git diff HEAD~1 -- app/db.py` produces no output. The file was imported and called but not modified.

---

## Forbidden Files Check

| File | Modified? | Status |
|------|-----------|--------|
| `static/index.html` | No | PASS |
| `app/db.py` | No | PASS |
| `docs/` (non-sprint) | No | PASS |

Only `app/models.py`, `app/main.py`, `tests/test_endpoints.py`, and `docs/sprints/sprint-1/session-2b-closeout.md` were touched. All within scope.

---

## Test Results

```
tests/test_endpoints.py: 10 passed (0.25s)
Full suite:              24 passed (0.23s)
No failures, no errors.
```

All pre-existing tests (14) continue to pass. 10 new tests added, matching the close-out report.

---

## Diff Review

The diff is clean and minimal:
- **app/models.py:** Five Pydantic models added to previously-stub file. Fields match the spec exactly.
- **app/main.py:** Stub endpoints replaced with real DB calls. Imports added for `get_events`, `get_clusters`, and the three response models. Function names changed from `get_events`/`get_clusters` (which shadowed the imported DB functions) to `list_events`/`list_clusters` -- a sensible rename to avoid name collision.
- **tests/test_endpoints.py:** 10 well-structured tests using mock patching at the correct import location (`app.main.get_events`/`app.main.get_clusters`).

---

## Notes

- The test for case-insensitive participant filtering (`test_get_events_participant_filter_case_insensitive`) verifies the endpoint passes the value through to `get_events` unchanged. It does not test that `ilike` itself performs case folding -- that is correctly treated as a `db.py` concern and would belong in `test_db.py` if tested at all. This boundary is appropriate.
- No scope creep detected. No deferred items were pulled in.

---

## Verdict: APPROVED

All spec requirements met. No regressions. No forbidden file modifications. Tests comprehensive and passing.
