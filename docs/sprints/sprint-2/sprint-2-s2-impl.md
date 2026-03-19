# Sprint 2, Session S2: Frontend Data Layer + Rendering

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `static/index.html` (the entire frontend — 1089 lines)
   - `app/models.py` (API response shapes: EventResponse, ClusterResponse)
   - `docs/sprints/sprint-2/sprint-spec.md` (acceptance criteria for deliverables 5 and 6)
   - `docs/design-reference.md` (color palette, typography, copy tone for empty state)
2. Run the test baseline:
   Scoped: `python -m pytest tests/test_endpoints.py -x -q`
   Expected: all passing (full suite confirmed by S3b close-out)
3. Verify you are on the correct branch
4. **Prerequisite:** Ensure at least 3-5 test events exist in the database (send via Telegram bot or Granola upload before starting). The visual verification requires real data.

## Objective
Replace all hardcoded data in `static/index.html` with live API fetches. Adapt both strata and resonance view rendering to work with the new data shape. Handle empty states.

## Requirements

### Data Fetching (replace hardcoded arrays)

1. **Remove** the hardcoded `EVENTS` array (lines ~315-382), the `CLUSTERS` array (lines ~282-289), and the `TC` tag→cluster mapping (lines ~303-311).

2. **Add async initialization:** Wrap all rendering setup in an async init function that:
   - Fetches `GET /events` → array of event objects
   - Fetches `GET /clusters` → array of cluster objects
   - If either fetch fails, shows an error message and stops
   - If events array is empty, shows the empty state and stops
   - Otherwise, proceeds to build data structures and start rendering

3. **Empty state:** When the events array is empty, display centered text: "The pattern is still forming" — in Cormorant Garamond italic, 24px, BONE color at 40% opacity. Hide the view toggle and axis labels. Do not initialize the canvas render loop.

### Data Transformation Layer

4. **Cluster mapping:** Build a lookup from cluster UUID → cluster object. Each cluster object should include:
   - `id` (UUID string)
   - `name` (string, e.g., "The Gate")
   - `glyph_id` (string, e.g., "dream" — maps to the existing GLYPHS object)
   - `col` (RGB array — mapped from glyph_id: dream/food → GOLD, silence/memory → VIOLET, body/writing → RIVER)
   - `event_count` (integer)
   - `myth_text` (string or null)
   - `cx`, `cy`, `r` (resonance layout positions — computed, not from API)

5. **Event mapping:** Transform each API event into the shape the rendering code expects:
   - `id` (UUID string)
   - `label` (string)
   - `note` (string or null)
   - `participant` (string)
   - `source` (string)
   - `xs` (float, from API — this is the semantic x-position)
   - `day` (integer — compute as days between this event's `created_at` and the earliest event's `created_at`)
   - `cluster` (reference to the cluster object, looked up via `cluster_id`)
   - `strataX`, `strataY` (computed from xs and day, same formula as current code)
   - `resX`, `resY` (computed from cluster position, same layout formula)

6. **Events with null cluster_id:** Filter these out of the rendering array. Log to console: `"Event ${id} has no cluster, hiding"`.

### Edge Array Construction

7. **Build edges from cluster co-membership:** For each pair of events in the same cluster, create an edge object:
   - `source` (event index in the rendered array)
   - `target` (event index)
   - `weight` (float: `1.0 / cluster.event_count` — smaller clusters = stronger bonds)
   - Only include edges where weight > 0.05 (skip very large clusters where individual connections are meaningless)
   - Limit to ~500 edges max to avoid performance issues (if more exist, take the highest-weight ones)
   - Each edge also needs the rendering properties the current code uses: `strataCpX/Y`, `resCp1x/y`, `resCp2x/y`, `ghostOff1/2` — compute these with the same deterministic pseudo-random formulas the prototype uses (based on source/target indices).

### Rendering Adaptation

8. **Glyph lookups:** Replace `GLYPHS[cl.id]` with `GLYPHS[cl.glyph_id]`. The GLYPHS object keys are already the glyph IDs (`dream`, `body`, `food`, `silence`, `memory`, `writing`). This is a key rename, not a restructure.

9. **Color lookups:** Replace `cl.col` direct references. Colors come from the glyph_id → color mapping defined above (requirement 4).

10. **Cluster functions:** Replace `primaryCluster(e.tags)` and `allClusters(e.tags)` — these are no longer needed since each event has a direct `cluster_id`. Replace with `e.cluster.glyph_id` for cluster identity checks.

11. **Resonance layout:** The current code hardcodes 6 cluster positions at fixed angles. Replace with dynamic layout:
    - Distribute N clusters evenly around the center at angles `i * (2π / N) - π/2`
    - Center radius: `Math.min(W, H) * 0.28` (same as current)
    - Cluster ring radius: proportional to event count (base 60, +2 per event, max 90)

12. **Strata layout:** Replace `DAYS` computation:
    - Compute `day` for each event from `created_at`
    - Build `DAYS` array from unique day values, sorted descending (most recent at top)
    - Strata positions computed the same way (day → y, xs → x)

13. **Axis labels:** Keep "inward · dream · solitude" and "social · food · connection" for now. These are semantic orientation markers, not data-driven.

14. **Day labels:** Replace `−Nd` format with actual dates or relative days from real `created_at` values.

15. **Tag similarity function:** Replace `tagSim(a, b)` — used for edge opacity and node hover glow. Replace with:
    - For nodes in the same cluster: similarity = weight from the edge array
    - For nodes in different clusters: similarity = 0
    - This simplifies the glow computation to cluster-based rather than tag-based

## Constraints
- Do NOT modify: any backend files (`app/`, `scripts/`, `tests/`)
- Do NOT change: the CSS styles at the top of index.html (preserve the visual design)
- Do NOT change: the HTML structure (panel, grain overlay, toggle buttons, UI container)
- Do NOT remove: the GLYPHS object (SVG glyph definitions) — it's still used, just accessed by glyph_id
- Do NOT add: any new HTML files, JS files, or build steps (DEC-005)
- Do NOT add: periodic polling or WebSocket connections
- Do NOT implement: participant colors or toggle (that's S4)
- Do NOT implement: panel content adaptation (that's S3c) — panels can be broken/empty after this session

## Visual Review
The developer should visually verify the following after this session:

1. **Page load with data:** Page loads without console errors. Events and clusters fetched (check Network tab).
2. **Empty state:** With an empty database, centered "The pattern is still forming" message displays in Cormorant Garamond italic.
3. **Strata view:** Events positioned on time×semantic grid. Day labels show real dates/relative days. Axis labels visible at bottom.
4. **Resonance view:** Events grouped in constellations around archetype centers. Cluster name labels visible above each constellation. Cluster rings visible.
5. **Transition:** Animated transition between strata and resonance views works smoothly.
6. **Node colors:** Nodes colored by archetype cluster (GOLD, VIOLET SLATE, RIVER — not yet participant colors, that's S4).
7. **Edges:** Connection lines visible between events in the same cluster. Lines have varying opacity based on weight.
8. **Node hover:** Hovering over a node highlights connected edges and shows the event label.
9. **Grain overlay:** Still visible at ~4% opacity over everything.

Verification conditions:
- Test with 5+ events in the database across at least 2 different clusters
- Also test with an empty database to verify empty state
- Test in Chrome or Firefox with dev tools open (Console tab for errors, Network tab for fetches)

## Definition of Done
- [ ] All hardcoded EVENTS, CLUSTERS, and TC arrays removed
- [ ] Async data fetch from /events and /clusters on page load
- [ ] Empty state shows "The pattern is still forming" when no events
- [ ] Events mapped correctly to cluster objects via cluster_id UUID
- [ ] xs read from API response (not computed client-side)
- [ ] day computed from created_at relative to earliest event
- [ ] Edge array built from cluster co-membership with weight
- [ ] Both strata and resonance views render with real data
- [ ] Animated transition between views works
- [ ] Glyph and color lookups work via glyph_id
- [ ] Node hover glow and edge highlighting work
- [ ] No console errors on load (with data and without data)
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| CSS styles unchanged | First ~200 lines of index.html identical to pre-session |
| HTML structure unchanged | Panel HTML, grain div, toggle buttons present |
| GLYPHS object preserved | All 6 glyph SVG functions still exist |
| View toggle works | Clicking strata/resonance buttons switches views |
| Grain overlay visible | Faint noise texture over everything |
| Canvas renders | No blank/black page — actual nodes and edges visible |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

**Write the close-out report to a file:**
docs/sprints/sprint-2/session-s2-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-2/review-context.md`
2. The close-out report path: `docs/sprints/sprint-2/session-s2-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest -x -q -n auto` (no frontend tests, but verify backend unbroken)
5. Files that should NOT have been modified: everything in `app/`, `tests/`, `scripts/`

The @reviewer will write its report to:
docs/sprints/sprint-2/session-s2-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS, follow the post-review fix documentation protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify NO hardcoded EVENTS array remains (search for the old array contents)
2. Verify NO hardcoded CLUSTERS array with mock positions remains
3. Verify NO tag→cluster mapping (TC object) remains
4. Verify xs is READ from the API response, not computed client-side
5. Verify edge array uses the generic {source, target, weight} structure (Sprint 3 data swap ready)
6. Verify empty state text is exactly "The pattern is still forming" (not a variant)
7. Verify no backend files modified
8. Verify events with null cluster_id are filtered out with console log

## Sprint-Level Regression Checklist (for @reviewer)
- [ ] All existing backend tests still pass
- [ ] No backend files modified
- [ ] CSS styles preserved
- [ ] HTML structure preserved
- [ ] GLYPHS object preserved

## Sprint-Level Escalation Criteria (for @reviewer)
- Canvas blank/black with data present → rendering regression
- Console errors from missing data fields → data transformation bug
- Transition animation broken → view state regression
