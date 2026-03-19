# Sprint 2, Session S3c: Frontend Panel Adaptation

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `static/index.html` (as modified by S2 — the data layer and rendering are now live)
   - `app/models.py` (MythRequest/MythResponse shapes from S3b)
   - `docs/sprints/sprint-2/sprint-spec.md` (acceptance criteria for deliverable 7)
   - `docs/design-reference.md` (copy tone, archetype glyphs section)
2. Run the test baseline:
   Scoped: `python -m pytest tests/test_endpoints.py tests/test_myth.py -x -q`
   Expected: all passing
3. Verify you are on the correct branch
4. **Prerequisite:** Ensure 5+ test events exist across at least 2 clusters for meaningful panel testing.

## Objective
Wire the event panel, archetype panel, and chained navigation to work with real API data. Replace the direct Anthropic API call with the backend `/myth` endpoint. Adapt neighbor list, spiral canvas, and glyph rendering.

## Requirements

### Event Panel (`openEventPanel`)

1. **Adapt data access:** The function currently accesses `e.tags`, `e.resCluster`, `DAYS[0]-e.day`, `tagSim()`. Replace with:
   - Cluster reference: `e.cluster` (set during data transformation in S2)
   - Day display: compute from `e.day` (already an integer from S2 data layer)
   - Participant: `e.participant` (new — not in prototype)
   - Note: `e.note` (from API)

2. **Glyph rendering in panel:** Replace `GLYPHS[cl.id]` with `GLYPHS[cl.glyph_id]` (the cluster object from S2 has a `glyph_id` field).

3. **Archetype link:** The glyph and archetype name in the event panel should be clickable → opens archetype panel. Use `cl.id` (UUID) as the argument to `openArchetypePanel`.

4. **Neighbor events:** Replace tag-based neighbor computation with cluster co-membership:
   - Find all other events in the same cluster
   - Sort by proximity (e.g., closest `day` values or random selection)
   - Take top 3
   - Each neighbor shows: mini glyph, label, archetype name
   - Each neighbor is clickable → opens their event panel (chained navigation)

5. **Remove tag display:** The prototype shows tags as small labels in the event panel. Since real events don't have tags, remove this display. Replace with participant name and source (e.g., "jessie · telegram").

### Archetype Panel (`openArchetypePanel`)

6. **Adapt data access:** The function currently uses `CLUSTERS.find(c=>c.id===clusterId)` with string IDs. Replace with UUID-based lookup from the cluster map built in S2.

7. **Event list for spiral:** `EVENTS.filter(e=>primaryCluster(e.tags)===clusterId)` → filter by `e.cluster.id === clusterId`.

8. **Glyph rendering:** `GLYPHS[clusterId]` → `GLYPHS[cluster.glyph_id]`.

9. **Metadata line:** `${clEvents.length} events · ${clusterId}` → `${clEvents.length} events · ${cluster.name}`.

10. **Spiral canvas:** The `makeSpiral` function receives cluster events. Verify it works with the new event shape:
    - Events must have `label`, `day` (or `created_at` for sorting), and `clusterSharedTags` (or a replacement metric)
    - Replace `clusterSharedTags` (was computed from tag overlap) with a simpler metric: all events in the same cluster get equal weight, or use recency (more recent = wider spiral loop)
    - Sort events by `created_at` (oldest first) instead of by `day`

### Myth Fetching (`fetchMyth`)

11. **Replace direct Anthropic API call:** The prototype calls `https://api.anthropic.com/v1/messages` directly from the browser. Replace with:
    ```javascript
    fetch('/myth', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({cluster_id: cluster.id})
    })
    ```
    - Parse response: `data.myth_text`
    - On error: display "The pattern holds."
    - Keep the client-side `mythCache` object for session-level caching (avoid repeated calls within same page load)

12. **Loading state:** Keep "reading the pattern…" as the loading indicator in the myth text area.

### Click Handlers

13. **Canvas click → event panel:** The `hovNode` detection uses event indices into the EVENTS array. Verify this still works with the dynamically-built event array from S2.

14. **Archetype name click → archetype panel:** The DOM click handlers on `.cluster-name` and `.strata-archetype` elements use cluster IDs. Verify these pass the UUID (not the old string ID).

15. **Panel close:** Verify `closePanel` stops spiral animation and clears panel content. Should work unchanged but verify.

## Constraints
- Do NOT modify: any backend files (`app/`, `scripts/`, `tests/`)
- Do NOT modify: the CSS styles section of index.html
- Do NOT modify: the data fetching or rendering code from S2 (only modify panel functions and myth fetching)
- Do NOT implement: participant colors in panels (that's S4)
- Do NOT implement: the individual/collective toggle (that's S4)

## Visual Review
The developer should visually verify:

1. **Event panel opens:** Click any event node → panel slides in from right with event data.
2. **Event panel content:** Shows label, note text, participant name, relative day, archetype glyph + name.
3. **Archetype link in event panel:** Click the glyph or archetype name → archetype panel opens (replacing event panel).
4. **Archetype panel opens:** Click any archetype name label → panel slides in with archetype data.
5. **Archetype panel content:** Shows glyph (72px), archetype name, myth text (loaded from /myth), event count, spiral canvas.
6. **Myth loading:** "reading the pattern…" shows briefly, then resolves to a mythic sentence in the ancestral register.
7. **Spiral canvas:** Renders with real events, animates (slow rotation), event labels visible on coil.
8. **Neighbor events:** Event panel shows 3 neighbors from same cluster, each clickable.
9. **Chained navigation:** Event → archetype → back to a different event via neighbor list. Full chain works.
10. **Panel close:** X button closes panel. Spiral animation stops (no orphaned animation frames).

Verification conditions:
- 5+ events across 2+ clusters
- Open panels for events in different clusters to test glyph/color variety
- Test chained navigation: event → archetype → neighbor → their archetype

## Definition of Done
- [ ] Event panel shows real data (label, note, participant, day, archetype)
- [ ] Archetype panel shows real data (name, glyph, events, myth, spiral)
- [ ] Myth text loaded from /myth endpoint (not direct Anthropic API)
- [ ] Chained navigation works (event → archetype → neighbor)
- [ ] Spiral canvas renders with real events
- [ ] No direct calls to api.anthropic.com remain in the frontend
- [ ] No console errors when opening/closing panels
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| Data layer from S2 intact | Both views still render correctly |
| View transition still works | Toggle between strata/resonance |
| No backend files modified | git diff shows only static/index.html |
| Grain overlay still visible | Check visual |

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

**Write the close-out report to a file:**
docs/sprints/sprint-2/session-s3c-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-2/review-context.md`
2. The close-out report path: `docs/sprints/sprint-2/session-s3c-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest -x -q -n auto` (verify backend unbroken)
5. Files that should NOT have been modified: everything in `app/`, `tests/`, `scripts/`

The @reviewer will write its report to:
docs/sprints/sprint-2/session-s3c-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS, follow the post-review fix documentation protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify NO direct calls to `api.anthropic.com` remain in the frontend code
2. Verify myth fetch uses `POST /myth` with `{cluster_id: uuid}` body
3. Verify neighbor computation uses cluster co-membership (not tag similarity)
4. Verify archetype panel passes UUID (not string ID like "dream") to functions
5. Verify spiral canvas `makeSpiral` works without `clusterSharedTags` property
6. Verify panel close stops spiral animation (check for `_stopAnim` or equivalent cleanup)

## Sprint-Level Regression Checklist (for @reviewer)
- [ ] All backend tests still pass
- [ ] No backend files modified
- [ ] Both views still render
- [ ] View transition still works

## Sprint-Level Escalation Criteria (for @reviewer)
- Panels crash on open → data shape mismatch from S2
- Myth endpoint returns errors → S3b integration issue
- Chained navigation breaks → UUID vs string ID confusion
