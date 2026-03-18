# Sprint 1, Session 3a: Embedding Pipeline (OpenAI Integration)

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/config.py`
   - `app/models.py`
   - `docs/architecture.md`
2. Run the test baseline:
   Scoped: `python -m pytest tests/test_endpoints.py tests/test_db.py -x -q`
   Expected: ~23 tests, all passing
3. Verify you are on the correct branch: `sprint-1` (or `main`)
4. Verify OPENAI_API_KEY is set and valid (can call text-embedding-3-small)

## Objective
Implement the `embed_text()` function using OpenAI's text-embedding-3-small model (1536 dimensions), with proper error handling, a typed exception class, and a mock-friendly architecture for testing.

## Requirements

1. Update `app/config.py`:
   - No new fields needed (OPENAI_API_KEY already defined in Session 1)
   - Verify the field exists — if Session 1 didn't add it, add it now

2. Update `requirements.txt`:
   - Add `openai` (Python SDK)

3. Create `app/embedding.py`:
   - Define `EmbeddingError(Exception)` — typed exception for embedding failures
   - `embed_text(text: str) -> list[float]`:
     - Calls OpenAI `client.embeddings.create(model="text-embedding-3-small", input=text)`
     - Returns the embedding vector as a list of floats
     - Raises `EmbeddingError` with descriptive message on any OpenAI API error
     - Handles empty string input without crashing (OpenAI handles this)
   - `embed_texts(texts: list[str]) -> list[list[float]]`:
     - Batch embedding for efficiency (Granola transcripts produce multiple segments)
     - Calls OpenAI with multiple inputs in a single API call
     - Returns list of embeddings in same order as inputs
     - Raises `EmbeddingError` on any failure (no partial results)
   - Use dependency injection or a module-level client for mock-friendliness:
     - Either accept an optional `client` parameter
     - Or provide a `get_embedding_client()` function that can be patched in tests

4. Create `tests/test_embedding.py`:
   - **Unit tests (mocked OpenAI client):**
     - Test embed_text returns list of 1536 floats (mocked response)
     - Test embed_text raises EmbeddingError on API failure
     - Test embed_texts with multiple inputs returns correct count
     - Test embed_texts with empty list returns empty list
   - **Live integration test (requires real API key):**
     - Mark with `@pytest.mark.integration` or `@pytest.mark.skipif(no API key)`
     - Test embed_text("hello world") returns exactly 1536 floats
     - Test that two different texts produce different embeddings
     - Verify embedding values are in a reasonable range (not all zeros, not all ones)

## Constraints
- Do NOT modify: `static/index.html`, any files under `docs/`
- Do NOT modify: `app/db.py`, `app/models.py`, `app/main.py` (no endpoints in this session)
- Do NOT add: clustering logic (that's Session 3b)
- Do NOT add: any API endpoints
- The embedding module must be usable without a database connection — it's pure computation + OpenAI API

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write: listed in Requirements #4
- Minimum new test count: 6
- Test command: `python -m pytest -x -q` (skips integration tests by default)
- Integration test command: `python -m pytest -x -q --run-integration` (or however the skip marker is configured)

## Definition of Done
- [ ] All requirements implemented
- [ ] embed_text("hello world") returns 1536 floats (live test)
- [ ] embed_texts(["a", "b"]) returns 2 embeddings (mocked test)
- [ ] EmbeddingError raised on API failure (mocked test)
- [ ] OpenAI client is mockable for unit tests
- [ ] All existing tests still pass
- [ ] All new tests pass
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Sprint-Level)
| Check | How to Verify |
|-------|---------------|
| Health endpoint returns 200 | `pytest tests/test_health.py -k health` |
| Health endpoint reports DB status | Verify "database" field in response |
| GET /events returns valid JSON on empty DB | `pytest tests/test_endpoints.py -k "events and empty"` |
| GET /events excludes embedding | Verify no "embedding" key in response |
| Embedding module has no DB dependency | Import app.embedding without DB connection |

## Sprint-Level Escalation Criteria
1. Supabase pgvector unavailable → STOP
2. Railway deployment fails 3+ consecutive times → STOP
3. **OpenAI embedding dimensions ≠ 1536 → STOP** (directly relevant to this session)
4. Degenerate cluster assignment (>80% to one cluster) → STOP
5. Cosine similarity uniformly > 0.95 or < 0.1 → STOP
6. Any session exceeds 2× estimated test count → STOP
7. supabase-py requires >20 lines raw SQL for vector ops → escalate
8. Telegram webhook needs different endpoint structure → escalate
9. Compaction in Session 4b → partial close-out + follow-up

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-1/session-3a-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-1/review-context.md`
2. The close-out report path: `docs/sprints/sprint-1/session-3a-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_embedding.py -x -q`
5. Files that should NOT have been modified: `static/index.html`, `app/db.py`, `app/models.py`, `app/main.py`, anything under `docs/` (except sprint reports)

The @reviewer will write its report to: docs/sprints/sprint-1/session-3a-review.md

## Session-Specific Review Focus (for @reviewer)
1. Verify embed_text returns exactly 1536 floats (not some other dimension)
2. Verify EmbeddingError is a proper typed exception (not bare Exception)
3. Verify OpenAI client is mockable (dependency injection or patchable function)
4. Verify embed_texts handles empty list input gracefully
5. Verify no database imports or dependencies in embedding.py
6. Verify the model string is "text-embedding-3-small" (not ada, not 3-large)
7. Check escalation criteria #3: confirm the returned dimension is 1536
