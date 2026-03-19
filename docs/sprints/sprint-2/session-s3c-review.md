# Tier 2 Review: Sprint 2, Session S3c — Frontend Panel Adaptation

**Reviewer:** Tier 2 automated review
**Date:** 2026-03-19
**Spec:** `docs/sprints/sprint-2/sprint-2-s3c-impl.md`
**Close-out:** `docs/sprints/sprint-2/session-s3c-closeout.md`

---

## Test Results

| Suite | Result |
|-------|--------|
| Full suite (`python -m pytest -x -q -k "not SeedClustersIntegration"`) | 118 passed, 3 skipped, 0 failed |

No regressions.

---

## Session-Specific Review

### 1. No direct calls to `api.anthropic.com` in frontend
**PASS.** Grep for `anthropic.com` in `static/index.html` returns zero matches. All myth fetching goes through the backend `/myth` endpoint.

### 2. Myth fetch uses `POST /myth` with `{cluster_id: uuid}` body
**PASS.** The `fetchMyth` function (line 898) calls `fetch('/myth', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({cluster_id:cl.id})})`. The `cl.id` value comes from `rc.id` (the raw cluster response UUID from `/clusters`). Response parsing extracts `data.myth_text` with fallback `'The pattern holds.'`. Client-side `mythCache` is preserved for session caching.

### 3. Neighbor computation uses cluster co-membership (not tag similarity)
**PASS.** The neighbor computation (line 816) filters by `ev.cluster.id !== cl.id` to find same-cluster events, then sorts by `Math.abs(ev.day - e.day)` (day proximity). The old edge-weight-based sorting (`edgeWeightMap.get(key)`) is fully removed. Neighbor opacity is set to a constant `0.8` rather than scaling by edge weight, which is a reasonable judgment call given that all neighbors share the same cluster.

### 4. Archetype panel passes UUID (not string ID) to functions
**PASS.** All call sites for `openArchetypePanel` pass `cl.id` or `a.id`, which originate from the API response UUID (`rc.id` at line 337). Specifically:
- Cluster name click handlers (line 532): `openArchetypePanel(cl.id)`
- Strata archetype click handlers (line 546): `openArchetypePanel(a.id)`
- Event panel glyph buttons (lines 873-874): `openArchetypePanel(cl.id)`

### 5. Spiral canvas `makeSpiral` works without `clusterSharedTags` property
**PASS.** Grep for `clusterSharedTags` returns zero matches in the file. The `makeSpiral` function (line 679) sorts events by `created_at` timestamp instead. The spiral rendering uses `loopH` computed from event count, not from any tag-overlap metric.

### 6. Panel close stops spiral animation
**PASS.** The animation cleanup chain is properly wired:
- `makeSpiral` stores cleanup as `sc._stopAnim = () => cancelAnimationFrame(animId)` (line 767)
- After mounting, the spiral reference is stored: `panel._stopSpiral = sc._stopAnim` (line 802)
- `closePanelFull` calls `panel._stopSpiral()` and nulls it (line 663)
- `openPanel` also calls `panel._stopSpiral()` before replacing content (line 668)
- The close button listener calls both `closePanel` and `_stopSpiral` cleanup (lines 649-653)

### 7. Archetype panel metadata shows `cl.name` (not `cl.glyph_id`)
**PASS.** Line 784 now reads `${clEvents.length} events \u00b7 ${cl.name}`. The diff confirms the change from `cl.glyph_id` to `cl.name`.

---

## Sprint-Level Regression Checklist

- [x] All backend tests still pass (118 passed, 3 skipped, 0 failed)
- [x] No backend files modified (only `static/index.html` changed; doc files have trivial path corrections only)
- [x] Both views still render (strata and resonance layout logic unchanged; `ARCHETYPES` built from `CLUSTERS`, event positioning intact)
- [x] View transition still works (toggle handlers at lines 632-647 unchanged; `closePanelFull` called on transition)

---

## Escalation Criteria Check

- Panels crash on open (data shape mismatch): **NO** (all panel functions use `e.cluster`, `cl.id`, `cl.name`, `cl.glyph_id` consistently with S2 data layer)
- Myth endpoint returns errors (S3b integration issue): **NO** (fetchMyth correctly calls `/myth` with UUID)
- Chained navigation breaks (UUID vs string ID): **NO** (all navigation paths use UUID from API response)
- 5+ existing tests fail: **NO** (0 failures)

No escalation needed.

---

## Concerns

None. The three changes are minimal, targeted, and correct. The session accurately identified the remaining gaps between spec and implementation, and the fixes are clean.

---

## Verdict

**APPROVED**

All seven session-specific review items pass. The diff contains exactly three focused changes: (1) spiral sort changed from `day` to `created_at`, (2) archetype metadata label changed from `glyph_id` to `name`, (3) neighbor computation changed from edge-weight sorting to day-proximity sorting with constant opacity. No backend files modified. All 118 tests pass. No regressions, no concerns.
