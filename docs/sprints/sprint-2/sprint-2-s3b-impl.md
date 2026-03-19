# Sprint 2, Session S3b: Myth Endpoint Wiring

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/main.py` (current route definitions, the `/myth` stub)
   - `app/myth.py` (the module implemented in S3a)
   - `app/models.py` (current Pydantic models)
   - `app/db.py` (database query functions)
   - `docs/sprints/sprint-2/sprint-spec.md` (acceptance criteria for deliverable 4)
2. Run the test baseline:
   Scoped: `python -m pytest tests/test_myth.py tests/test_endpoints.py -x -q`
   Expected: all passing (full suite confirmed by S3a close-out)
3. Verify you are on the correct branch

## Objective
Wire the myth generation module into the FastAPI `/myth` endpoint. Replace the stub that returns `{"myth": ""}` with a working handler that calls `get_or_generate_myth`.

## Requirements

1. **In `app/models.py`:** Add request and response models:
   - `MythRequest(BaseModel)` with field `cluster_id: UUID`
   - `MythResponse(BaseModel)` with fields `myth_text: str` and `cached: bool`

2. **In `app/main.py`:** Replace the `/myth` POST stub:
   - Accept `MythRequest` as the request body
   - Call `get_or_generate_myth(str(request.cluster_id))`
   - Return `MythResponse(myth_text=text, cached=is_cached)`
   - Handle errors:
     - If cluster_id not found in database: return 404 with `{"error": "cluster_not_found"}`
     - If request body is missing or malformed: return 400 (FastAPI handles this automatically with Pydantic validation)
     - If myth generation fails unexpectedly: return 503 with `{"error": "myth_generation_failed"}`, log the error
   - Import `get_or_generate_myth` from `app.myth`

3. **CORS:** Verify the existing CORS middleware allows POST to `/myth` from the frontend origin. It should — the current config allows all origins. Just confirm, don't change.

## Constraints
- Do NOT modify: `app/telegram.py`, `app/granola.py`, `app/embedding.py`, `app/myth.py` (already complete from S3a), `static/index.html`, `app/config.py`
- Do NOT change: any existing endpoint behavior. Only the `/myth` endpoint changes (from stub to functional).
- Do NOT add: any new endpoints beyond wiring the existing `/myth` stub.

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write:
  1. `POST /myth` with valid cluster_id returns 200 with myth_text and cached fields (mock `get_or_generate_myth`)
  2. `POST /myth` with non-existent cluster_id returns 404 (mock DB lookup returning None)
  3. `POST /myth` with missing body returns 422 (Pydantic validation error)
  4. `POST /myth` with malformed cluster_id (not a UUID) returns 422
  5. `POST /myth` cache hit: verify `cached: true` in response (mock returning cached myth)
  6. `POST /myth` handles generation failure gracefully (mock raising exception → 503)
- Minimum new test count: 4
- Test file: extend `tests/test_endpoints.py` or create `tests/test_myth_endpoint.py`
- Test command: `python -m pytest tests/test_endpoints.py -x -q`

## Definition of Done
- [ ] `MythRequest` and `MythResponse` models added to models.py
- [ ] `/myth` POST endpoint functional (stub replaced)
- [ ] 404 for unknown cluster_id
- [ ] 503 for generation failure with error logged
- [ ] All existing tests pass
- [ ] 4+ new tests written and passing
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| All other endpoints unchanged | GET /events, GET /clusters, POST /telegram, POST /granola, GET /health all still work |
| CORS middleware unchanged | Check main.py CORS config is identical |
| myth.py not modified | git diff shows no changes to app/myth.py |
| App startup still works | health check passes |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-2/session-s3b-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-2/review-context.md`
2. The close-out report path: `docs/sprints/sprint-2/session-s3b-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_endpoints.py tests/test_myth.py -x -q`
5. Files that should NOT have been modified: `app/telegram.py`, `app/granola.py`, `app/embedding.py`, `app/myth.py`, `app/config.py`, `static/index.html`

The @reviewer will write its report to:
docs/sprints/sprint-2/session-s3b-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS, follow the post-review fix documentation protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify the `/myth` stub is replaced, not duplicated (only one `/myth` route)
2. Verify 404 response for unknown cluster_id (not 500, not empty 200)
3. Verify MythRequest uses UUID type for cluster_id (not str)
4. Verify error handling: generation failure returns 503 with error logged, not unhandled exception
5. Verify no other endpoints were modified

## Sprint-Level Regression Checklist (for @reviewer)
- [ ] All existing passing tests still pass
- [ ] All endpoints except /myth behave identically
- [ ] No prohibited files modified

## Sprint-Level Escalation Criteria (for @reviewer)
- 5+ existing tests fail → stop and assess
- /myth endpoint changes break other endpoints → regression investigation
