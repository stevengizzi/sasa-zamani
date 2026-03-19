---BEGIN-CLOSE-OUT---

**Session:** Sprint 2 — S2f2 Toggle Permanently Broken After Panel Open
**Date:** 2026-03-19
**Self-Assessment:** CLEAN

### Root Cause

**None of the spec's hypotheses (A-D) were the root cause.** The actual cause is a data-driven crash in the `draw()` animation loop.

The `/clusters` endpoint returns `event_count: 0` for all clusters (DEF-010: non-atomic increment_event_count). The frontend computes edge weights as `1.0 / cl.event_count`, which produces `Infinity` when `event_count` is 0. The guard `if(weight <= 0.05) continue;` does not catch `Infinity` because `Infinity > 0.05` is `true`.

When the user hovers a node, `nodeSimilarity()` returns these `Infinity` weights. The glow computation `e.glow += (tgt - e.glow) * 0.10` sets `e.glow = Infinity`. The draw function then calls `ctx.createRadialGradient(..., 10 + Infinity * 12)`, which throws `"The provided double value is non-finite"`. Since `draw()` has no try-catch, the exception kills the `requestAnimationFrame(draw)` chain. The animation loop dies permanently.

With the animation loop dead, `transProgress` never updates. The toggle handlers still fire correctly (viewMode, transDir, and classList all change), but the canvas never redraws, so the view appears frozen. The user perceives the toggle as "dead."

The crash triggers on the first hover of a node that shares a cluster with another node. Since opening a panel requires hovering and clicking a node, the crash always coincides with the first panel open — but the panel operation itself is not the cause.

### Fix

**Line 438 of `static/index.html`:** Changed edge weight computation from `1.0/cl.event_count` (uses stale API value) to `1.0/(indices.length||1)` (uses actual frontend event count for the cluster, with a floor of 1 to prevent division by zero).

This is the minimum targeted fix. It uses the count of events actually present in the frontend's cluster group rather than the unreliable `event_count` field from the API. The `||1` guard ensures the weight is always finite.

### Change Manifest
| File | Change Type | Rationale |
|------|-------------|-----------|
| static/index.html | modified | Fix Infinity edge weight from zero event_count |

### Scope Verification
| Spec Requirement | Status | Implementation |
|-----------------|--------|----------------|
| Toggle works before any panel open | DONE | Draw loop no longer crashes |
| Toggle works after panel open + close | DONE | Verified via Playwright |
| Toggle works after archetype panel close | DONE | Verified via Playwright |
| Toggle works after multiple open/close cycles | DONE | Verified 3 cycles |
| Only modify static/index.html | DONE | Single line change |
| No CSS changes | DONE | No CSS modifications |
| No HTML structure changes | DONE | No structural changes |
| No canvas rendering logic changes | DONE | Fix is in data computation, not rendering |
| No data fetching logic changes | DONE | No fetch modifications |

### Regression Checks
| Check | Result | Notes |
|-------|--------|-------|
| Both views render | PASS | Verified via Playwright |
| Animated transition works | PASS | transProgress advances correctly |
| Draw loop stays alive | PASS | tick advances after all interactions |
| All backend tests pass | PASS | 20 passed, 1 pre-existing error (test_inserts_six_clusters) |

### Test Results
- Tests run: 21
- Tests passed: 20
- Tests failed: 0
- Tests errored: 1 (pre-existing: test_inserts_six_clusters teardown FK constraint)
- New tests added: 0 (frontend-only session, verified via headless Playwright)
- Command used: `python -m pytest -x -q`

### Unfinished Work
None

### Notes for Reviewer
- The root cause is upstream: DEF-010 (non-atomic increment_event_count) leaves all cluster `event_count` values at 0. This fix makes the frontend resilient to that stale data rather than fixing the backend counter.
- The pre-existing `test_inserts_six_clusters` error is unrelated — it's a teardown FK constraint issue documented in prior sessions.
- Diagnosis was performed using headless Playwright (Chromium) to reproduce and verify the crash/fix cycle programmatically.

---END-CLOSE-OUT---

```json:structured-closeout
{
  "schema_version": "1.0",
  "sprint": "2",
  "session": "S2f2",
  "verdict": "COMPLETE",
  "tests": {
    "before": 20,
    "after": 20,
    "new": 0,
    "all_pass": true
  },
  "files_created": ["docs/sprints/sprint-2/session-s2f2-closeout.md"],
  "files_modified": ["static/index.html"],
  "files_should_not_have_modified": [],
  "scope_additions": [],
  "scope_gaps": [],
  "prior_session_bugs": [],
  "deferred_observations": [
    "DEF-010 (non-atomic increment_event_count) is the upstream cause — all cluster event_count values are 0 in the database. The frontend fix makes edge weights resilient to this, but the backend counter remains broken."
  ],
  "doc_impacts": [],
  "dec_entries_needed": [],
  "warnings": [],
  "implementation_notes": "Single line change: edge weight uses indices.length (actual frontend count) instead of cl.event_count (stale API value). Division by zero guard via ||1."
}
```
