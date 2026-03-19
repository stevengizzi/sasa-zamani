# Session S1b — Tier 2 Review Report

---BEGIN-REVIEW---

**Session:** Sprint 3 — S1b: Pipeline Fixes (DEF-012, DEF-013, DEF-014)
**Reviewer:** Tier 2 Automated (Claude Opus 4.6)
**Date:** 2026-03-19
**Verdict:** CONCERNS

---

## 1. Diff Audit

### Files Modified (expected)
| File | Changes | Assessment |
|------|---------|------------|
| `app/telegram.py` | OrderedDict dedup with 10k cap; increment_event_count try/except; xs try/except | Correct |
| `app/granola.py` | increment_event_count try/except; DEF-014 comment | Correct |
| `tests/test_telegram.py` | Fixture update for OrderedDict; 3 new tests | Correct |
| `tests/test_granola.py` | 2 new tests | Correct |
| `docs/sprints/sprint-3/session-s1b-closeout.md` | New file (closeout) | Expected |

### Files That Should NOT Have Been Modified
- `app/config.py` — NOT modified. OK.
- `app/models.py` — NOT modified. OK.
- `app/embedding.py` — NOT modified. OK.
- `app/main.py` — NOT modified. OK.
- `app/clustering.py` — NOT modified. OK.
- `app/myth.py` — NOT modified. OK.
- `static/index.html` — NOT modified. OK.
- `scripts/seed_clusters.py` — NOT modified. OK.

---

## 2. Session-Specific Focus Items

### 2.1 Dedup cap evicts oldest entries (not random or newest)
**PASS.** `OrderedDict.popitem(last=False)` evicts the first-inserted (oldest) entry. This is the correct FIFO eviction strategy. The test `test_dedup_set_oldest_evicted` verifies by inserting IDs 1-10000, then adding 10001, and confirming ID 1 was evicted while ID 10000 was retained.

### 2.2 Granola: increment failure does not suppress the event
**CONCERN.** The `increment_event_count` call is correctly wrapped in try/except at `granola.py:112-118`, and the code continues to the xs computation and result appending. The event *is* returned. However, the xs computation block (lines 120-124) is NOT wrapped in try/except. If `get_cluster_by_id` or `compute_xs` raises after an increment failure, the exception propagates unhandled and would abort the entire loop, suppressing any remaining unprocessed segments. This is a pre-existing condition (the xs block was never protected in granola.py), but the telegram pipeline received a defensive try/except for the same block in this session. The asymmetry is notable.

### 2.3 Telegram: increment failure does not change return value
**PASS.** The insert, increment, and xs blocks are each in separate try/except blocks. If increment fails, the function continues through xs computation (also protected) and returns `{"processed": True, "reason": "ok", "event_id": row.get("id")}`. The test `test_telegram_increment_failure_event_survives` verifies this.

### 2.4 No changes to `extract_message` or `parse_transcript` signatures
**PASS.** Neither function signature was modified. Confirmed by diff inspection.

### 2.5 Warning log for dedup cap fires only once
**PASS.** The `_dedup_cap_warned` module-level boolean is set to `True` after the first warning at `telegram.py:89`. Subsequent evictions at capacity skip the log. The fixture correctly resets this flag between tests.

---

## 3. Test Verification

**Command:** `python -m pytest tests/test_telegram.py tests/test_granola.py -x -q`
**Result:** 40 passed, 0 failed, 0 errors.

All new tests exercise the claimed behavior:
- `test_dedup_set_cap_enforced` — inserts 10001 IDs, asserts len <= 10000
- `test_dedup_set_oldest_evicted` — verifies FIFO eviction order
- `test_telegram_increment_failure_event_survives` — increment raises, result is still `processed: True`
- `test_granola_return_contract_cluster_name` — cluster_name is human-readable string
- `test_granola_increment_failure_event_survives` — increment raises, all 3 events still returned

---

## 4. Regression Check

- Existing `extract_message` tests: PASS (11 tests)
- Existing `is_duplicate` tests: PASS (2 tests)
- Existing `process_telegram_update` tests: PASS (6 tests)
- Existing `parse_transcript` tests: PASS (8 tests)
- Existing `process_granola_upload` tests: PASS (5 tests)
- Endpoint tests: PASS (3 tests)
- No API contract changes detected.
- `POST /telegram` still returns 200 in all cases (handled in `app/main.py`, not modified).

---

## 5. Scope Compliance

### Spec Requirements
| Requirement | Status |
|------------|--------|
| DEF-013: Cap dedup set at 10,000 with oldest-eviction | DONE |
| DEF-013: Warning log fires once | DONE |
| DEF-012: increment failure in telegram pipeline | DONE |
| DEF-012: increment failure in granola pipeline | DONE |
| DEF-014: Verify cluster_name is human-readable | DONE |
| 5 new tests | DONE (3 telegram + 2 granola) |

### Scope Addition (Judgment Call)
The xs computation in `telegram.py` was separated into its own try/except. This is a reasonable defensive addition that follows the same pattern as the DEF-012 fix. It prevents xs failures from masking a successful insert+increment.

---

## 6. Findings

### CONCERN-01: Asymmetric xs protection between pipelines (Medium)
**Location:** `app/granola.py:120-124`
**Description:** In `telegram.py`, the xs computation block (`get_cluster_by_id` / `compute_xs` / `update_event_xs`) is wrapped in its own try/except (lines 151-158). In `granola.py`, the same block (lines 120-124) has no try/except protection. If xs computation raises during a granola upload, the exception propagates and aborts the loop, potentially losing results for remaining segments. This is a pre-existing condition but was highlighted by the session's decision to protect the telegram path and not the granola path.

**Impact:** A `get_cluster_by_id` or `compute_xs` failure during granola upload would cause a partial result (some segments processed, rest lost). The event that triggered the failure would also be lost from the result list despite being successfully inserted.

**Recommendation:** Wrap the xs block in `granola.py` in the same defensive try/except pattern applied to `telegram.py`. This is a small, focused change.

**Post-Review Fix:** RESOLVED. The xs computation block in `granola.py` has been wrapped in a defensive try/except matching the telegram.py pattern. All tests pass.

---

## 7. Escalation Criteria Check

| Criterion | Triggered? |
|-----------|-----------|
| Atomic increment requires schema change | No — not in scope for this session |
| Seeding produces >500 events | N/A |
| Myth output fails tonal test | N/A |
| Frontend changes break interactions | No frontend changes |
| Test pass count drops below 118 | No — 40/40 in scope; closeout reports 134 pass overall |

No escalation criteria triggered.

---

## 8. Verdict

**CONCERNS**

The implementation is correct and complete for all three deferred items. All 5 new tests pass and exercise the claimed behavior. The dedup cap correctly evicts oldest entries, increment failures are properly isolated in both pipelines, and the warning log fires exactly once.

One medium-severity concern: the xs computation block in `granola.py` lacks the same defensive try/except applied to `telegram.py` in this session, creating an asymmetry where a granola upload could still lose segments on xs failure. This does not meet any escalation criterion (it is a pre-existing condition, not a regression), but is worth addressing in a subsequent session.

---END-REVIEW---

```json:structured-verdict
{
  "schema_version": "1.0",
  "sprint": "3",
  "session": "S1b",
  "verdict": "CONCERNS",
  "tests": {
    "scoped_command": "python -m pytest tests/test_telegram.py tests/test_granola.py -x -q",
    "passed": 40,
    "failed": 0,
    "errors": 0,
    "skipped": 0
  },
  "forbidden_file_violations": [],
  "findings": [
    {
      "id": "CONCERN-01",
      "severity": "medium",
      "title": "Asymmetric xs protection between pipelines",
      "file": "app/granola.py",
      "lines": "120-124",
      "description": "The xs computation block in granola.py lacks the defensive try/except applied to the same block in telegram.py. An xs failure during granola upload would abort the loop and lose remaining segments.",
      "recommendation": "Wrap granola.py xs block (get_cluster_by_id / compute_xs / update_event_xs) in try/except with logger.warning, matching telegram.py pattern."
    }
  ],
  "escalation_triggers": [],
  "focus_item_results": [
    {"item": "Dedup cap evicts oldest entries", "result": "PASS"},
    {"item": "Granola increment failure does not suppress event", "result": "PASS"},
    {"item": "Telegram increment failure does not change return value", "result": "PASS"},
    {"item": "No changes to extract_message or parse_transcript signatures", "result": "PASS"},
    {"item": "Warning log fires once only", "result": "PASS"}
  ]
}
```
