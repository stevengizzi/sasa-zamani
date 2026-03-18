# Tier 2 Review: Sprint 1 — Session 4a (Telegram Webhook Handler)

**Reviewer:** @reviewer (Claude)
**Date:** 2026-03-18
**Verdict:** PASS_WITH_NOTES

---

## Review Focus Checklist

| # | Focus Item | Verdict | Notes |
|---|-----------|---------|-------|
| 1 | POST /telegram ALWAYS returns 200 (never 4xx or 5xx) | PASS | The endpoint wraps `process_telegram_update` in a try/except that catches all exceptions and returns `{"ok": False, "error": "internal_error"}` with HTTP 200. Invalid JSON also returns 200. Test `test_post_telegram_returns_200_on_internal_error` confirms this. |
| 2 | No partial writes: if embedding fails, no event row exists | PASS | `process_telegram_update` returns before any DB call when `embed_text` raises `EmbeddingError`. Pipeline order is strictly: embed -> assign -> (insert_event + increment_event_count). No DB writes occur until embedding and cluster assignment both succeed. |
| 3 | Duplicate update_id handling is functional | PASS | `is_duplicate` uses an in-memory set. First call adds the ID and returns False; second call finds it and returns True. Tests `test_is_duplicate_first_call_returns_false` and `test_is_duplicate_second_call_returns_true` confirm. Pipeline calls `is_duplicate` before any embedding or DB work. |
| 4 | Unknown Telegram users map to "unknown" (not crash) | PASS | `extract_message` uses `PARTICIPANT_MAP.get(username, "unknown")`. Test `test_extract_message_unknown_username` confirms an unrecognized username yields participant `"unknown"`. Missing `from` field defaults to `{}` via `.get("from", {})`. |
| 5 | Non-text messages are skipped gracefully | PASS | `extract_message` returns None when `message.get("text")` is None. Test `test_extract_message_photo_returns_none` sends a photo-only update and confirms None return. Whitespace-only text also returns None. |
| 6 | Seed clusters confirmed present before first event processing | PASS | `_ensure_seed_clusters()` is called in the lifespan handler after `ensure_schema()` and before the app yields (accepts requests). It calls `seed_clusters(get_db())` which is idempotent. |
| 7 | embedding.py and clustering.py were not modified (only imported) | PASS | `git diff HEAD~1 --name-only` shows only: `app/main.py`, `app/telegram.py`, `tests/conftest.py`, `tests/test_telegram.py`, `docs/sprints/sprint-1/session-4a-closeout.md`. Neither `app/embedding.py` nor `app/clustering.py` appears. |
| 8 | Pipeline order: extract -> dedup -> embed -> assign -> store -> increment | PASS | `process_telegram_update` lines 70-113 follow this exact sequence. Each step returns early on failure, preventing subsequent steps from executing. |

## Forbidden File Check

| File | Modified? | Verdict |
|------|-----------|---------|
| `static/index.html` | No | PASS |
| `app/embedding.py` | No | PASS |
| `app/clustering.py` | No | PASS |
| `app/db.py` (signatures) | No | PASS |
| `docs/` (non-sprint) | No | PASS |

Files changed in this commit: `app/main.py` (modified), `app/telegram.py` (modified), `tests/conftest.py` (modified), `tests/test_telegram.py` (added), `docs/sprints/sprint-1/session-4a-closeout.md` (added). All within scope.

## Test Results

```
15 passed, 1 warning in 0.51s  (tests/test_telegram.py)
62 passed, 3 skipped, 1 warning in 0.58s  (full suite)
```

- 15 new tests added for telegram module (12 unit, 3 endpoint)
- 3 skipped tests are pre-existing embedding integration tests (no real API key)
- 0 failures
- Full suite regression: all 62 tests pass

## Findings

### ISSUE-1: Non-atomic insert_event + increment_event_count (severity: low)

In `process_telegram_update` lines 98-108, `insert_event` and `increment_event_count` are two separate DB calls within the same try/except block. If `insert_event` succeeds but `increment_event_count` fails, the event row exists in the database but the cluster's `event_count` is stale. The function returns `{"processed": False, "reason": "db_failed"}`, which is misleading since the event was already written.

This is low severity for v1 because: (a) `increment_event_count` is a simple update unlikely to fail independently, (b) `event_count` is a denormalized counter that can be recomputed, and (c) the spec does not require transactional atomicity for the counter. However, a future session should consider wrapping both calls in a Supabase RPC or at minimum logging which step failed.

### ISSUE-2: increment_event_count has a read-modify-write race condition (severity: low, pre-existing)

`db.py:increment_event_count` reads the current count, adds 1 in Python, then writes back. Under concurrent requests this could lose increments. This is pre-existing code (not introduced in this session) and acceptable for v1 single-process deployment. Noting for completeness.

### ISSUE-3: Spec contradiction on embedding failure HTTP status (severity: note)

The sprint spec (review-context.md line 69) states "OpenAI failure -> 503, no event stored" while the session-specific review focus states "POST /telegram ALWAYS returns 200." The implementation correctly returns 200 in all cases, which is the right choice for a Telegram webhook (non-200 causes retry storms). The spec entry should be amended to clarify that the 503 behavior does not apply to the Telegram endpoint.

## Observations

1. **PARTICIPANT_MAP is empty:** The map contains no entries. All Telegram users will be assigned `"unknown"` until this is populated. The close-out correctly flags this as a pre-production requirement. Not blocking.

2. **In-memory dedup set grows unbounded:** `_processed_update_ids` is never pruned. For v1 with low message volume this is fine, but over weeks/months of uptime it will consume memory linearly. A bounded set (e.g., LRU with max size, or periodic clearing) should be considered for production hardening.

3. **Logger created at import time vs. request time:** In `app/main.py:telegram_webhook`, a logger is created inside the function body on every request (`logging.getLogger("app.telegram")`). This is harmless (loggers are cached by name) but unconventional. The logger could be a module-level constant. Minor style point, not blocking.

4. **Close-out test count discrepancy:** The structured close-out JSON reports `"before": 35, "after": 50, "new": 15` but the full suite runs 62 tests (not 50). The "before" count of 35 does not match the 47 from session 3b either. The prose section correctly states "Tests run: 62, Tests passed: 62." The structured JSON appears to have stale numbers. Not a functional issue.

## Close-out Report Accuracy

The close-out report is mostly accurate. Self-assessment of MINOR_DEVIATIONS is confirmed. The structured JSON test counts are inconsistent with both the prose section and actual test results (62 total, not 50). All scope items are correctly marked as DONE. The judgment calls are reasonable and well-documented.

---

**Verdict: PASS_WITH_NOTES** — All eight review focus items satisfied. No forbidden files modified. Tests pass. Pipeline order is correct. The endpoint always returns HTTP 200 as required. Two low-severity issues identified (non-atomic DB writes, spec contradiction on 503) — neither is blocking. The structured close-out test counts should be corrected.
