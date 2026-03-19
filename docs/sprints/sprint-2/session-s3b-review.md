# Tier 2 Review: Sprint 2, Session S3b — Myth Endpoint Wiring

**Reviewer:** Tier 2 automated review
**Date:** 2026-03-19
**Spec:** `docs/sprints/sprint-2/sprint-2-s3b-impl.md`
**Close-out:** `docs/sprints/sprint-2/session-s3b-closeout.md`

---

## Test Results

| Suite | Result |
|-------|--------|
| `tests/test_endpoints.py tests/test_myth.py` | 32 passed |
| Full suite (`python -m pytest -x -q`) | 118 passed, 3 skipped, 0 failed |

No regressions.

---

## Session-Specific Review

### 1. `/myth` stub replaced, not duplicated
**PASS.** Exactly one `@app.post("/myth")` route exists in `app/main.py` (line 127). The stub returning `{"myth": ""}` is gone, replaced with a working handler that calls `get_or_generate_myth`.

### 2. 404 response for unknown cluster_id
**PASS.** The handler catches `ValueError` and returns `JSONResponse(status_code=404, content={"error": "cluster_not_found"})`. Test `test_post_myth_returns_404_for_unknown_cluster` confirms this path.

### 3. MythRequest uses UUID type for cluster_id
**PASS.** `MythRequest` in `app/models.py` (line 43-44) declares `cluster_id: UUID`. Test `test_post_myth_returns_422_for_malformed_uuid` confirms Pydantic rejects non-UUID strings with 422.

### 4. Error handling: generation failure returns 503 with error logged
**PASS.** The handler catches generic `Exception`, logs via `myth_logger.error()` before returning `JSONResponse(status_code=503, content={"error": "myth_generation_failed"})`. Test `test_post_myth_returns_503_on_generation_failure` confirms this path.

### 5. No other endpoints modified
**PASS.** Diff shows no changes to the route definitions for `/`, `/events`, `/clusters`, `/telegram`, `/granola`, or `/health`. The only import additions are `MythRequest`, `MythResponse`, and `get_or_generate_myth`.

### 6. PROHIBITED_WORDS includes "unlock" and "activate"
**PASS.** `app/myth.py` line 16 now includes `"activate"`, line 17 includes `"unlock"`. `"activation"` is retained alongside `"activate"`. Diff confirms these are the only changes to `myth.py`.

### 7. Delta test differentiation
**PASS.** `test_returns_true_when_delta_gte_3` now calls `should_regenerate("cluster-1", 6)` with `event_count_at_generation=2`, giving delta=4. `test_returns_true_when_delta_exactly_3` calls with `5`, giving delta=3. The two tests now exercise distinct cases.

---

## Sprint-Level Regression Checklist

- [x] All existing passing tests still pass (118 passed, 3 skipped, 0 failed)
- [x] All endpoints except /myth behave identically (no changes to other routes)
- [x] No prohibited files modified (`app/telegram.py`, `app/granola.py`, `app/embedding.py`, `app/config.py`, `static/index.html` all unchanged)
- [x] myth.py changes limited to PROHIBITED_WORDS constant only (confirmed via diff)

---

## Escalation Criteria Check

- 5+ existing tests fail: **NO** (0 failures)
- /myth endpoint changes break other endpoints: **NO** (all other endpoint tests pass)

No escalation needed.

---

## Concerns

### CONCERN-1: Return type annotation mismatch (LOW)

The `generate_myth` handler is annotated `-> MythResponse` and declares `response_model=MythResponse`, but the error paths return `JSONResponse` (for 404 and 503). This is a type annotation inaccuracy. FastAPI handles it correctly at runtime because `JSONResponse` bypasses the `response_model` serialization, so behavior is correct. However, a static type checker would flag the mismatch.

The existing `/granola` endpoint uses the same `JSONResponse` pattern but avoids the issue by not declaring a return type annotation. Consistency would suggest either removing the `-> MythResponse` annotation or using `-> MythResponse | JSONResponse`.

**Impact:** None at runtime. Low-priority cleanup. Does not block approval.

### CONCERN-2: Inline imports inside function body (INFORMATIONAL)

The handler imports `logging` and `JSONResponse` inside the function body rather than at module level. This follows the existing pattern established by the `/granola` endpoint. `JSONResponse` is already imported at module level (line 9: `from fastapi.responses import FileResponse`... actually it is not -- `FileResponse` is imported, not `JSONResponse`). `logging` is a stdlib module. No performance concern but slightly inconsistent with the top-level import of `get_or_generate_myth`.

**Impact:** None. Follows existing codebase convention. Informational only.

---

## Verdict

**APPROVED_WITH_CONCERNS**

All spec requirements are met. All tests pass. No regressions. No prohibited files modified. The two S3a review fixes (PROHIBITED_WORDS and delta test differentiation) are correctly applied. The concerns are low-severity style issues that do not affect correctness.

### Summary of Concerns
| ID | Severity | Description |
|----|----------|-------------|
| CONCERN-1 | LOW | Return type annotation `-> MythResponse` does not account for JSONResponse error paths |
| CONCERN-2 | INFORMATIONAL | Inline imports follow existing pattern but could be hoisted to module level |
