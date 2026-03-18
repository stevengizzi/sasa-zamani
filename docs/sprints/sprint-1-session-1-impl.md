# Sprint 1, Session 1: Project Scaffold + Configuration + Health Endpoint

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `CLAUDE.md`
   - `docs/architecture.md`
   - `docs/project-knowledge.md`
2. Run the test baseline:
   Full suite: `python -m pytest -x -q` (expect 0 tests — greenfield project)
3. Verify you are on the correct branch: `main` (or create `sprint-1` branch)
4. Confirm required env vars are available: SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, TELEGRAM_BOT_TOKEN
5. Confirm Python 3.12 is the runtime

## Objective
Stand up the FastAPI project structure, configuration system using Pydantic Settings (env vars), and a running app with a health endpoint. Verify it deploys to Railway.

## Requirements

1. Create `app/__init__.py` — empty init file for the app package.

2. Create `app/config.py` — Pydantic Settings class loading from environment:
   - `supabase_url: str` (required)
   - `supabase_key: str` (required)
   - `openai_api_key: str` (required)
   - `telegram_bot_token: str` (required)
   - `cluster_join_threshold: float = 0.3`
   - Use `model_config = SettingsConfigDict(env_file=".env")` for local development
   - Provide a `get_settings()` function with `@lru_cache` for singleton access

3. Create `app/main.py` — FastAPI application:
   - App instance with title="Sasa/Zamani API", version="0.1.0"
   - `GET /health` endpoint returning `{"status": "healthy"}` (DB check comes in Session 2a)
   - `GET /` returning `{"message": "Sasa/Zamani API"}` as a minimal root response
   - Import settings at startup to fail fast on missing env vars

4. Create `requirements.txt` with pinned versions:
   - fastapi
   - uvicorn[standard]
   - pydantic-settings
   - python-dotenv
   - pytest
   - httpx (for FastAPI test client)

5. Create `.env.example` with all required env vars as placeholders (no real values).

6. Create `Procfile` for Railway:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

7. Create `tests/__init__.py` — empty init file.

8. Create `tests/conftest.py`:
   - Fixture for FastAPI test client using httpx.AsyncClient
   - Fixture that sets mock env vars for testing (so tests don't require real API keys)

9. Create `tests/test_health.py`:
   - Test GET /health returns 200
   - Test GET /health response includes "status" key
   - Test GET / returns 200 with message
   - Test that settings load correctly from env vars
   - Test that missing required env var raises validation error

## Constraints
- Do NOT modify: `static/index.html` (prototype frontend — untouched until Sprint 2)
- Do NOT modify: any files under `docs/`
- Do NOT add: database connection logic (that's Session 2a)
- Do NOT add: any API endpoints beyond /health and /
- Do NOT add: Docker configuration
- Do NOT add: CI/CD configuration

## Test Targets
After implementation:
- Existing tests: N/A (greenfield)
- New tests to write: listed in Requirements #9
- Minimum new test count: 5
- Test command: `python -m pytest -x -q`

## Definition of Done
- [ ] All requirements implemented
- [ ] `uvicorn app.main:app` starts without error (with env vars set)
- [ ] Missing env var produces clear Pydantic validation error at startup
- [ ] All tests pass
- [ ] Code pushed to GitHub
- [ ] Railway deployment attempted (note result in close-out — may need manual setup)
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Sprint-Level)
| Check | How to Verify |
|-------|---------------|
| Health endpoint returns 200 | `python -m pytest tests/test_health.py -k health` |
| App starts cleanly with all env vars | `uvicorn app.main:app` exits 0 on ctrl-c |
| App fails fast on missing env vars | Remove SUPABASE_URL, verify startup error |

## Sprint-Level Escalation Criteria
1. Supabase pgvector unavailable → STOP
2. Railway deployment fails 3+ consecutive times → STOP
3. OpenAI embedding dimensions ≠ 1536 → STOP
4. Degenerate cluster assignment (>80% to one cluster) → STOP
5. Cosine similarity uniformly > 0.95 or < 0.1 → STOP
6. Any session exceeds 2× estimated test count → STOP
7. supabase-py requires >20 lines raw SQL for vector ops → escalate
8. Telegram webhook needs different endpoint structure → escalate
9. Compaction in Session 4b → partial close-out + follow-up

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout. See the close-out skill for the
full schema and requirements.

**Write the close-out report to a file:**
docs/sprints/sprint-1/session-1-closeout.md

Do NOT just print the report in the terminal. Create the file, write the
full report (including the structured JSON appendix) to it, and commit it.

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-1/review-context.md`
2. The close-out report path: `docs/sprints/sprint-1/session-1-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest -x -q`
5. Files that should NOT have been modified: `static/index.html`, anything under `docs/` (except sprint reports)

The @reviewer will produce its review report (including a structured JSON
verdict fenced with ```json:structured-verdict) and write it to:
docs/sprints/sprint-1/session-1-review.md

## Session-Specific Review Focus (for @reviewer)
1. Verify Pydantic Settings class has all five config fields with correct types and defaults
2. Verify .env.example lists all required vars
3. Verify health endpoint response format matches spec: {"status": "healthy"}
4. Verify conftest.py mocks env vars so tests don't require real API keys
5. Verify no database or external API code leaked into this session
