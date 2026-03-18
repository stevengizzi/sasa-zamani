# Sprint 1, Session 4c: Cleanup + Integration Hardening

## Context
This is a cleanup session addressing issues tracked by the Sprint 1 Work Journal. No new features. All changes are small, independent, and low-risk.

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/db.py`
   - `app/clustering.py`
   - `app/telegram.py`
   - `app/main.py`
   - `tests/test_clustering.py`
2. Run the test baseline:
   `python -m pytest -x -q`
   Expected: 87 tests collected, 84 pass, 3 skipped
3. Verify you are on the correct branch: `sprint-1` (or `main`)
4. Verify `OPENAI_API_KEY` is set in `.env`
5. Check Supabase connectivity: `python -c "from app.db import check_connection; print(check_connection())"` — if this returns False or errors, skip Task 4 and note it in the close-out.

## Tasks

### Task 1: Wrap ensure_schema() error message (Work Journal #5)

**File:** `app/db.py`

`ensure_schema()` currently probes tables with raw supabase-py calls. If a table is missing, the exception is opaque. Wrap the probe loop in a try/except that catches the supabase exception and re-raises with a clear message:

```python
def ensure_schema() -> None:
    """Verify database schema exists by probing tables."""
    client = get_db()
    for table in ("clusters", "events", "myths"):
        try:
            client.table(table).select("id", count="exact").limit(0).execute()
        except Exception as exc:
            raise RuntimeError(
                f"Table '{table}' not found. Run scripts/init_supabase.sql in "
                f"the Supabase SQL editor to create the schema."
            ) from exc
```

**Test:** Add a test in `tests/test_db.py` that mocks a failed table probe and asserts the RuntimeError message contains "init_supabase.sql".

### Task 2: Remove unused db_client param from seed_clusters() (Work Journal #10)

**Files:** `app/clustering.py`, `app/main.py`

`seed_clusters(db_client)` accepts a `db_client` parameter but never uses it — it imports `cluster_exists` and `insert_cluster` via lazy imports. Remove the parameter.

In `app/clustering.py`, change:
```python
def seed_clusters(db_client) -> None:
```
to:
```python
def seed_clusters() -> None:
```

In `app/main.py`, change:
```python
seed_clusters(get_db())
```
to:
```python
seed_clusters()
```

**Test:** Existing tests should continue to pass. Verify no other callers pass the argument (search the codebase for `seed_clusters(`).

### Task 3: Populate PARTICIPANT_MAP with real identities (Work Journal #17)

**File:** `app/telegram.py`

The current `extract_message` looks up participants by Telegram username only:
```python
from_user = message.get("from", {})
username = from_user.get("username", "")
participant = PARTICIPANT_MAP.get(username, "unknown")
```

Two of three participants (Jessie and Steven) don't have Telegram usernames — only first names and last names appear in the webhook payload. Modify the lookup to try `username` first, then full name (`first_name last_name`), then `first_name` alone:

```python
PARTICIPANT_MAP: dict[str, str] = {
    # By Telegram username (without @)
    "emma_murf": "emma",
    # By full name (first_name + last_name from Telegram)
    "Jessie Lian": "jessie",
    "Steven Gizzi": "steven",
    "Emma Murphy": "emma",
    # By first_name alone (fallback)
    "Jessie": "jessie",
    "Steven": "steven",
    "Emma": "emma",
}
```

Update `extract_message` participant lookup (around lines 46-48) to:
```python
from_user = message.get("from", {})
username = from_user.get("username", "")
first_name = from_user.get("first_name", "")
last_name = from_user.get("last_name", "")
full_name = f"{first_name} {last_name}".strip()
participant = (
    PARTICIPANT_MAP.get(username)
    or PARTICIPANT_MAP.get(full_name)
    or PARTICIPANT_MAP.get(first_name, "unknown")
)
```

The lookup chain: username → full name → first name → "unknown". Each `.get()` without a default returns `None` on miss, so the `or` falls through. Only the final `first_name` lookup defaults to `"unknown"`.

**Tests:** Add to `tests/test_telegram.py`:
- `test_extract_message_emma_by_username`: payload with `"username": "emma_murf"` → participant `"emma"`
- `test_extract_message_jessie_by_full_name`: payload with no username, `"first_name": "Jessie"`, `"last_name": "Lian"` → participant `"jessie"`
- `test_extract_message_steven_by_full_name`: payload with no username, `"first_name": "Steven"`, `"last_name": "Gizzi"` → participant `"steven"`
- `test_extract_message_first_name_fallback`: payload with no username, `"first_name": "Jessie"`, no last_name → participant `"jessie"`
- `test_extract_message_username_takes_precedence`: payload with both a mapped username AND a mapped full name → participant matches the username mapping

### Task 4: Fill clustering integration test stubs (Work Journal #12)

**File:** `tests/test_clustering.py`

**Prerequisite:** Task 4 depends on a working Supabase connection. If the pre-flight Supabase check failed, SKIP this task entirely and note it in the close-out.

The three stub tests in `TestSeedClustersIntegration` currently have `pass` bodies. These require real Supabase + real OpenAI. Fill them in:

- `test_inserts_six_clusters`: Call `seed_clusters()` with real OpenAI embeddings, then call `get_clusters()` and assert 6 clusters with the correct names.
- `test_idempotent`: Call `seed_clusters()` twice, assert `get_clusters()` still returns exactly 6 (not 12).
- `test_get_clusters_returns_six`: After seeding, call `get_clusters()` and verify each cluster has `name`, `id`, `event_count == 0`, and `is_seed == True`.

These tests must be marked `@pytest.mark.integration` (already are on the class). They should clean up after themselves if possible — delete the test clusters at teardown. If supabase-py doesn't support delete easily, document this in the close-out.

**Important:** These tests will call the real OpenAI API. Set `OPENAI_API_KEY` (not `OPENAI_API_KEY_REAL`) for these since they run through `seed_clusters()` which uses the standard settings path. You'll need to temporarily bypass or work around the conftest `mock_env_vars` autouse fixture for these tests — either by reading the real key from `.env` and re-setting it, or by using a separate conftest override. Document your approach in the close-out.

### Task 5: Live cluster assignment sanity check (Work Journal #22 / RSK-001)

Write and run a one-off script `scripts/cluster_sanity.py` that:
1. Embeds a set of test messages using real OpenAI embeddings
2. Computes seed centroids via `compute_seed_centroids()`
3. Runs `assign_cluster()` against each message
4. Reports the assigned cluster and similarity score for each

**Test messages:**
```python
test_messages = [
    ("We cooked dinner together and shared stories around the table", "The Table"),
    ("I dreamt I was standing at a door that kept moving further away", "The Gate"),
    ("Went swimming at dawn, the water remembered my body before I did", "What the Body Keeps"),
    ("Sat alone for an hour. Said nothing. It was enough.", "The Silence"),
    ("My grandmother used to say that word differently", "The Root"),
    ("Spent the morning writing field notes about yesterday", "The Hand"),
]
```

For each message, print:
- The message text (truncated to 60 chars)
- Expected cluster
- Actual assigned cluster
- Similarity score
- MATCH / MISMATCH flag

Then print a summary: X/6 matched expected cluster.

This is a data point for RSK-001 (embedding quality), not a hard pass/fail gate. Even 4/6 matches would be informative. The output will be pasted into the Work Journal for sprint close-out.

## Constraints
- Do NOT modify: `static/index.html`, any files under `docs/` (except sprint reports)
- Do NOT modify: `app/embedding.py`, `app/models.py`, `app/granola.py`
- Changes to `app/db.py`, `app/clustering.py`, `app/telegram.py`, `app/main.py` are scoped to the specific fixes above — do not refactor beyond what's specified
- No new endpoints, no new features

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests: ~6 (1 for ensure_schema error, 5 for participant mapping)
- Integration tests (Task 4): 3 filled-in stubs (if Supabase available)
- Test command: `python -m pytest -x -q`

## Close-Out
Write the close-out report to: `docs/sprints/sprint-1/session-4c-closeout.md`

Include:
- Which tasks were completed vs skipped
- The cluster sanity test output (full table from Task 5)
- RSK-001 assessment based on the results
- Any issues discovered during cleanup

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

## Tier 2 Review (Mandatory — @reviewer Subagent)
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-1/review-context.md`
2. The close-out report path: `docs/sprints/sprint-1/session-4c-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest -x -q`
5. Files that should NOT have been modified: `static/index.html`, `app/embedding.py`, `app/models.py`, `app/granola.py`, anything under `docs/` (except sprint reports)

The @reviewer will write its report to: `docs/sprints/sprint-1/session-4c-review.md`

## Session-Specific Review Focus (for @reviewer)
1. Verify ensure_schema() raises RuntimeError with "init_supabase.sql" in the message
2. Verify seed_clusters() no longer accepts a db_client parameter
3. Verify PARTICIPANT_MAP has entries for all three participants (emma, jessie, steven)
4. Verify extract_message tries username first, then full name, then first_name alone
5. Verify no modifications to files outside the constraint list
6. If Task 4 was completed: verify integration tests actually call real services (not mocked)
7. If Task 4 was skipped: verify it's documented in close-out with reason
