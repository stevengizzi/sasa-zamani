# Session 4c Tier 2 Review

**Reviewer:** @reviewer
**Date:** 2026-03-18
**Commit range:** Uncommitted changes on `sprint-1` (parent: `9c6a96b`)

---

## Test Results

```
90 passed, 3 skipped (0.55s)
```

No regressions. 6 new tests added (1 in `test_db.py`, 5 in `test_telegram.py`), matching close-out claim.

---

## Review Focus Checklist

| # | Item | Verdict | Evidence |
|---|------|---------|----------|
| 1 | `ensure_schema()` raises `RuntimeError` with `"init_supabase.sql"` in message | PASS | `app/db.py:37-40` — try/except wraps each table probe; `RuntimeError` raised with `"init_supabase.sql"` in the format string. Test `test_ensure_schema_raises_on_missing_table` asserts `pytest.raises(RuntimeError, match="init_supabase.sql")`. |
| 2 | `seed_clusters()` no longer accepts a `db_client` parameter | PASS | `app/clustering.py:131` — signature is `def seed_clusters() -> None:`. Call site in `app/main.py:35` is `seed_clusters()` with no args. Unused `get_db` import removed from `main.py` line 13. |
| 3 | `PARTICIPANT_MAP` has entries for all three participants (emma, jessie, steven) | PASS | `app/telegram.py:11-22` — 7 entries: `emma_murf` (username), `Jessie Lian` / `Steven Gizzi` / `Emma Murphy` (full names), `Jessie` / `Steven` / `Emma` (first-name fallbacks). All three participants covered. |
| 4 | `extract_message` tries username first, then full name, then first_name alone | PASS | `app/telegram.py:59-63` — chain is `PARTICIPANT_MAP.get(username) or PARTICIPANT_MAP.get(full_name) or PARTICIPANT_MAP.get(first_name, "unknown")`. Tests verify: username precedence (`test_extract_message_username_takes_precedence`), full-name lookup (`test_extract_message_jessie_by_full_name`, `test_extract_message_steven_by_full_name`), first-name fallback (`test_extract_message_first_name_fallback`). |
| 5 | No modifications to forbidden files | PASS | `git diff --name-only` for `static/`, `app/embedding.py`, `app/models.py`, `app/granola.py` returns empty. Only modified files: `app/db.py`, `app/clustering.py`, `app/telegram.py`, `app/main.py`, `tests/test_db.py`, `tests/test_telegram.py`. |
| 6 | Task 4 (integration test stubs): if completed, tests call real services | N/A | Task 4 was skipped. See item 7. |
| 7 | Task 4 skipped: documented in close-out with reason | PASS | Close-out states: "Skipped — Supabase connectivity check returned False at pre-flight; stubs left as-is." Structured JSON includes `"status": "skipped", "reason": "Supabase connectivity unavailable"`. |

---

## Additional Observations

**Clean changes.** All diffs are minimal and focused. No unnecessary refactoring or unrelated modifications.

**`ensure_schema` error wrapping is correct.** The `from exc` clause preserves the original traceback, which is good practice. The error message names the SQL script and the table that failed, giving operators clear guidance.

**Participant lookup chain has a subtle edge case.** If a Telegram user has an empty string username (i.e., `"username": ""`), `PARTICIPANT_MAP.get("")` returns `None` (no key `""`), so the chain falls through to full name correctly. This is fine.

**`cluster_sanity.py` is a useful one-off script.** It calls real OpenAI and real clustering logic. The close-out documents 6/6 matches with reasonable similarity scores. The script is well-structured and has no side effects on the database.

**No issues found.**

---

## Verdict

**PASS**
