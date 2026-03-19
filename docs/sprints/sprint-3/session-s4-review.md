```markdown
---BEGIN-REVIEW---

**Reviewing:** [Sprint 3.S4] — Frontend Demo Polish
**Reviewer:** Tier 2 Automated Review
**Date:** 2026-03-19
**Verdict:** CLEAR

### Assessment Summary
| Category | Result | Notes |
|----------|--------|-------|
| Scope Compliance | PASS | Only `static/index.html` modified. No `app/`, `tests/`, or `scripts/` files touched. All 5 spec requirements implemented. |
| Close-Out Accuracy | PASS | Change manifest matches actual diff. Judgment calls documented (DOM event list, edge fade derivation, lerp rate, error message text). Self-assessment of MINOR_DEVIATIONS is justified. |
| Test Health | PASS | 147 passed, 3 skipped, 3 errors (pre-existing FK teardown). Matches close-out report exactly. Above hard floor of 118. |
| Regression Checklist | PASS | No rendering logic altered beyond time-axis data source and fade interpolation. Panel open/close, view transitions, color encoding, participant toggle all structurally unchanged. |
| Architectural Compliance | PASS | Single-file frontend architecture preserved. No new dependencies. No new API calls. No schema changes. |
| Escalation Criteria | NONE_TRIGGERED | No existing interactions broken. Test count well above 118. No protected files modified. |

### Findings

**[INFO] Edge fade behavioral change:**
The previous edge fade logic used three discrete tiers: matching pair (1.0), mixed pair (0.4), non-matching pair (0.10). The new logic derives edge fade as `Math.min(ea.fadeCurrent, eb.fadeCurrent)`, which means cross-participant edges (one match, one non-match) now fade to ~0.15 instead of 0.4. This is a visual change, not a bug — the close-out documents this as a judgment call. The result is that edges connecting a matching and non-matching node are less visible than before, which is arguably more intuitive (the edge fades to match its dimmest endpoint).

**[INFO] Lerp asymptotic behavior:**
The fade interpolation `e.fadeCurrent += (fadeTarget - e.fadeCurrent) * 0.12` is an exponential ease-out that asymptotically approaches the target but never exactly reaches it. At 60fps with factor 0.12, after ~20 frames (~333ms) the value is within 0.07 of the target, which is visually imperceptible. This is standard for animation lerps and does not cause flicker. The `fadeCurrent` is initialized to 1 on event creation (line 473), so there is no flash on first render.

**[INFO] Esc handler safety:**
The Esc keydown listener is guarded by `panelOpen` (line 714). There are no `<input>`, `<textarea>`, or `contenteditable` elements in the frontend, so there is no risk of interfering with text input. The handler does not call `preventDefault()` or `stopPropagation()`, so it won't block browser-level Esc behavior (e.g., exiting fullscreen).

**[INFO] Reverse chaining correctness:**
Events are identified by their index in the `EVENTS` array, stored as `data-event-idx` attribute (line 879). The index is resolved via `EVENTS.indexOf(ev)` where `ev` is a direct object reference from `EVENTS.filter(...)` (line 862), so reference equality is guaranteed. The click handler bounds-checks the parsed index (`!isNaN(idx) && idx >= 0 && idx < EVENTS.length`) before calling `openEventPanel`. This is robust and avoids label-based ambiguity.

**[INFO] Loading state cleanup:**
The `removeLoadingState()` function uses `el.remove()` (line 563) to fully remove the DOM element, not just hide it. It is called in three code paths: success (line 568 in `buildDOM`), fetch error (line 362), and empty data (line 368). All exit paths are covered.

**[INFO] `event_date` fallback:**
The time axis now uses `e.event_date || e.created_at` in three locations: timestamp computation (line 401), per-event day calculation (line 413), and day label formatting (line 632). The fallback is consistent across all three. Events without `event_date` will seamlessly use `created_at`.

**[LOW] Loading state pulse animation inconsistency:**
The loading-state div uses `animation: pulse 2s ease-in-out infinite` (line 227) while the existing empty-state message uses `animation: pulse 1.5s ease-in-out infinite` (line 182). Both reference the same `@keyframes pulse` definition. The different durations are not a bug but are a minor visual inconsistency. The loading state pulses slower than the empty state.

**[LOW] `EVENTS.indexOf` is O(n) per event in archetype panel:**
In `openArchetypePanel`, each event in the cluster calls `EVENTS.indexOf(ev)` (line 877), which is O(n) per call. For a cluster with k events and n total events, this is O(k*n). With ~393 events and ~65 per cluster, this is ~25K comparisons — negligible for this scale. Would only matter if event count grew to thousands, which is not in scope.

### Recommendation
Proceed to next session. All five requirements are correctly implemented. No functional issues found. The two LOW findings are cosmetic/performance observations that do not require action at current scale.

---END-REVIEW---
```

```json:structured-verdict
{
  "schema_version": "1.0",
  "sprint": "3",
  "session": "S4",
  "verdict": "CLEAR",
  "findings": [
    {
      "description": "Edge fade behavioral change: cross-participant edges now fade to ~0.15 instead of previous 0.4 due to Math.min derivation",
      "severity": "INFO",
      "category": "OTHER",
      "file": "static/index.html",
      "recommendation": "No action needed — documented judgment call, visually coherent"
    },
    {
      "description": "Lerp asymptotic behavior: fadeCurrent never exactly reaches target, but is imperceptible after ~333ms",
      "severity": "INFO",
      "category": "PERFORMANCE",
      "file": "static/index.html",
      "recommendation": "No action needed — standard animation pattern"
    },
    {
      "description": "Loading state pulse animation uses 2s duration vs empty state's 1.5s — minor visual inconsistency",
      "severity": "LOW",
      "category": "OTHER",
      "file": "static/index.html",
      "recommendation": "Consider unifying pulse durations in a future polish pass"
    },
    {
      "description": "EVENTS.indexOf called per event in archetype panel is O(k*n) — negligible at current scale (~393 events)",
      "severity": "LOW",
      "category": "PERFORMANCE",
      "file": "static/index.html",
      "recommendation": "No action needed at current scale; consider index map if events grow to thousands"
    }
  ],
  "spec_conformance": {
    "status": "CONFORMANT",
    "notes": "All 5 spec requirements implemented correctly. event_date fallback, Esc handler, reverse chaining, fade animation, and loading state all match spec.",
    "spec_by_contradiction_violations": []
  },
  "files_reviewed": [
    "static/index.html",
    "docs/sprints/sprint-3/session-s4-closeout.md",
    "docs/sprints/sprint-3/sprint-3-session-s4-impl.md"
  ],
  "files_not_modified_check": {
    "passed": true,
    "violations": []
  },
  "tests_verified": {
    "all_pass": true,
    "count": 147,
    "new_tests_adequate": true,
    "test_quality_notes": "No new tests expected — frontend-only Canvas session. 147 passed, 3 skipped, 3 pre-existing errors (FK teardown). Above hard floor of 118."
  },
  "regression_checklist": {
    "all_passed": true,
    "results": [
      {"check": "No app/tests/scripts files modified", "passed": true, "notes": "git diff HEAD~1 confirms only static/index.html and docs/ changed"},
      {"check": "Test suite baseline maintained", "passed": true, "notes": "147 passed, 3 skipped, 3 errors — matches close-out"},
      {"check": "event_date fallback consistent", "passed": true, "notes": "Used in 3 locations: timestamps, day calc, day labels"},
      {"check": "Esc handler safe", "passed": true, "notes": "Guarded by panelOpen, no text inputs exist"},
      {"check": "Reverse chaining by index not label", "passed": true, "notes": "Uses EVENTS array index via data-event-idx attribute"},
      {"check": "Loading state removed from DOM", "passed": true, "notes": "el.remove() called in all 3 exit paths"},
      {"check": "No new global variables", "passed": true, "notes": "Only new function removeLoadingState and per-event fadeCurrent property"},
      {"check": "Panel open/close unchanged", "passed": true, "notes": "closePanel/closePanelFull logic not modified"},
      {"check": "Color encoding unchanged", "passed": true, "notes": "PARTICIPANT_COLORS and GLYPH_COLOR untouched"}
    ]
  },
  "escalation_triggers": [],
  "recommended_actions": []
}
```
