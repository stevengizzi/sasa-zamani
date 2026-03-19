# Tier 2 Review: Sprint 2, Session S2 — Frontend Data Layer + Rendering

**Reviewer:** Tier 2 automated review
**Date:** 2026-03-19
**Spec:** `docs/sprints/sprint-2/sprint-2-s2-impl.md`
**Close-out:** `docs/sprints/sprint-2/session-s2-closeout.md`

---

## Test Results

| Suite | Result |
|-------|--------|
| Full suite (`python -m pytest -x -q`) | 118 passed, 3 skipped, 0 failed |

No regressions.

---

## Session-Specific Review

### 1. No hardcoded EVENTS array remains
**PASS.** Searched for old array contents (`arrived`, `first dinner here`, tag arrays). No matches. The `EVENTS` variable is declared as an empty array at line 284 and populated exclusively from the `/events` API fetch in `init()`.

### 2. No hardcoded CLUSTERS array with mock positions remains
**PASS.** Searched for `{id:'dream'`, `{id:'body'`, etc. No matches. The old `CLUSTERS` array, `CLUSTER_ANGLES` constant, and fixed-position `forEach` loop are all removed. `CLUSTERS` is declared empty at line 283 and populated from `/clusters` API data with dynamically computed positions.

### 3. No tag-to-cluster mapping (TC object) remains
**PASS.** Searched for `TC`, `tagSim`, and `tag.*cluster` patterns. No matches. The `TC` object and `tagSim` function are fully removed. Similarity is now cluster-based via `nodeSimilarity()` (line 909) using `edgeWeightMap`.

### 4. xs is READ from API response, not computed client-side
**PASS.** Line 375: `xs:e.xs!=null?e.xs:0.5`. The `xs` value comes directly from the API event object. The fallback to `0.5` for null values is a reasonable defensive default. No client-side xs computation exists.

### 5. Edge array uses generic {source, target, weight} structure
**PASS WITH NOTE.** The candidate edge array (line 442) correctly uses `{source, target, weight}`. The final `EDGES` array (line 449) renames these to `{a, b, s}` for rendering compatibility with the prototype's drawing code. The close-out documents this deviation. The rename happens in a single `.map()` call, making Sprint 3 data swap straightforward -- the `/edges` endpoint response can be mapped to `{a, b, s}` in the same location.

### 6. Empty state text is exactly "The pattern is still forming"
**PASS.** Line 497: `msg.textContent='The pattern is still forming';` -- exact match. Styled in Cormorant Garamond italic, 24px, BONE color at 40% opacity per spec. View toggle and title are hidden.

### 7. No backend files modified
**PASS.** `git diff HEAD --name-only -- app/ tests/ scripts/` returns empty. Only `static/index.html` was modified.

### 8. Events with null cluster_id filtered out with console log
**PASS.** Line 362: `if(!e.cluster_id){console.log(`Event ${e.id} has no cluster, hiding`);return false;}` -- exact match to spec requirement. Additionally filters events whose `cluster_id` does not exist in the cluster map (line 363).

---

## Sprint-Level Regression Checklist

- [x] All existing backend tests still pass (118 passed, 3 skipped, 0 failed)
- [x] No backend files modified (confirmed via git diff)
- [x] CSS styles preserved (lines 1-179 unchanged; first diff hunk starts at line 215 in the script section)
- [x] HTML structure preserved (panel, grain, toggle buttons all present at lines 181-198, unchanged)
- [x] GLYPHS object preserved (all 6 glyph SVG functions confirmed: dream, body, food, silence, memory, writing)

---

## Escalation Criteria Check

- Canvas blank/black with data present: **NO** -- `draw()` loop with `requestAnimationFrame` is intact (line 1088), node and edge rendering code is complete
- Console errors from missing data fields: **NO** -- all data field accesses use the mapped event/cluster objects with appropriate null guards
- Transition animation broken: **NO** -- `transProgress`/`transDir` logic preserved, `easeInOut` function unchanged, strata/resonance position interpolation intact

No escalation needed.

---

## Concerns

### CONCERN-1: Edge field names use a/b/s instead of source/target/weight (LOW)

The spec requires "edge array uses the generic {source, target, weight} structure" for Sprint 3 data swap readiness. The implementation renames these to `a/b/s` in the final EDGES array (line 449-460) for compatibility with the rendering code. The close-out documents this as a judgment call.

The rename is localized to a single `.map()` call, so Sprint 3 can trivially swap the data source. However, using the canonical field names throughout and updating the rendering references would have been cleaner and would reduce the mapping step when the `/edges` endpoint is introduced.

**Impact:** Minimal. One extra mapping step in Sprint 3. Does not block approval.

### CONCERN-2: Dead variable `daysAgo` in day label construction (INFORMATIONAL)

Line 583: `const daysAgo=DAYS[DAYS.length-1]===d?0:DAYS[0]-d;` computes a value that is never used. The actual label text (line 589) computes `DAYS[0]-d` inline. This is dead code.

**Impact:** None. Minor cleanup opportunity.

### CONCERN-3: No direct Anthropic API calls from browser (PASS, not a concern)

Confirmed: no references to `anthropic.com` or `api.anthropic` in the frontend. Myth text is fetched exclusively via the backend `/myth` POST endpoint (line 890). Pre-populated myth text from the `/clusters` response is used when available (line 883), reducing unnecessary network calls.

---

## Verdict

**APPROVED**

All 8 session-specific review focus items pass. All sprint-level regression checks pass. The implementation correctly replaces all hardcoded data with async API fetches, preserves the CSS/HTML structure, maintains both rendering views with animated transitions, and handles empty state and null cluster_id edge cases per spec. The two concerns are low-severity and do not affect correctness or functionality.

### Summary of Concerns
| ID | Severity | Description |
|----|----------|-------------|
| CONCERN-1 | LOW | Edge field names use a/b/s instead of spec's source/target/weight |
| CONCERN-2 | INFORMATIONAL | Dead variable `daysAgo` in day label construction |
