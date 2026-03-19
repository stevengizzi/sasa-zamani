# Sprint 2, Session S4: Participant Colors + Toggle + Polish

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `static/index.html` (as modified by S2 + S3c — data layer, rendering, and panels all live)
   - `docs/sprints/sprint-2/sprint-spec.md` (acceptance criteria for deliverables 8, 9, 10)
   - `docs/design-reference.md` (participant colors section, copy tone)
2. Run the test baseline:
   Full suite: `python -m pytest -x -q -n auto`
   Expected: all tests passing (this is the final session — full suite baseline)
3. Verify you are on the correct branch
4. **Prerequisite:** Ensure test events exist from multiple participants (at least 2 of: jessie, emma, steven).

## Objective
Add participant color encoding to event nodes, build the individual/collective toggle with opacity fade, and perform final cleanup to ensure zero mock data remains.

## Requirements

### Participant Color Mapping

1. **Define participant color constants** in the JavaScript (near the existing color constants):
   ```javascript
   const PARTICIPANT_COLORS = {
     jessie: [127, 119, 221],   // #7F77DD
     emma: [216, 90, 48],       // #D85A30
     steven: [29, 158, 117],    // #1D9E75
     shared: [186, 117, 23],    // #BA7517
   };
   const DEFAULT_PARTICIPANT_COLOR = [228, 232, 228]; // BONE fallback
   ```

2. **Add CSS variables** for participant colors (in the `<style>` section):
   ```css
   :root {
     --color-jessie: #7F77DD;
     --color-emma: #D85A30;
     --color-steven: #1D9E75;
     --color-shared: #BA7517;
   }
   ```

3. **Node rendering:** In the draw loop where nodes are rendered (the `EVENTS.forEach` block that draws circles), change the node fill color:
   - Currently: node color is determined by cluster archetype color (`cl.col`)
   - New: node color is determined by `PARTICIPANT_COLORS[e.participant.toLowerCase()]` or `DEFAULT_PARTICIPANT_COLOR` if unknown
   - Keep cluster archetype colors for: edges, cluster rings, cluster name labels, glyph colors, node glow on hover
   - Only the node dot itself changes to participant color

4. **Event panel participant indicator:** In `openEventPanel`, add the participant name with a color dot:
   ```html
   <div class="ep-participant">
     <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:${participantHex};margin-right:6px;"></span>
     ${e.participant} · ${e.source}
   </div>
   ```
   Style in DM Mono, 9px, same as other metadata.

### Individual/Collective Toggle

5. **Toggle HTML:** Add a toggle UI element near the existing view toggle (bottom of screen). Position it to the right of the view toggle or in the top-right corner. Style:
   - DM Mono, 9px, letter-spacing 0.14em
   - Same border style as view toggle (0.5px solid rgba(196,154,58,0.25))
   - Buttons: "ALL", "JESSIE", "EMMA", "STEVEN"
   - Active button: participant color background at 6% opacity, participant color text
   - Inactive buttons: BONE at 30% opacity
   - The toggle element must have `pointer-events: all` (like the view toggle)

6. **Toggle state:** Add a state variable:
   ```javascript
   let activeParticipant = 'all'; // 'all' | 'jessie' | 'emma' | 'steven'
   ```

7. **Toggle click handlers:** Each button sets `activeParticipant` and updates button active states.

8. **Opacity fade logic:** In the draw loop:
   - If `activeParticipant === 'all'`: all events render at normal opacity (no change)
   - If a specific participant is selected:
     - Events matching `e.participant.toLowerCase() === activeParticipant`: render at full opacity
     - Other events: render at ~15% opacity (multiply all alpha values by 0.15)
     - Edges: if both endpoints are faded, edge fades to ~10% opacity. If one endpoint matches, edge renders at ~40% opacity. If both match, full opacity.
     - Cluster name labels and rings: unaffected (always visible)
     - Event labels on hover: only show for non-faded events

9. **Toggle persistence across view transition:** The `activeParticipant` state must persist when switching between strata and resonance views. The toggle buttons should not reset.

### Final Cleanup

10. **Search and destroy mock data:** Grep the entire index.html for any remnants:
    - No hardcoded event objects with `tags` arrays
    - No `TC` mapping object
    - No `primaryCluster(e.tags)` calls
    - No `allClusters(e.tags)` calls
    - No `tagSim(a.tags, b.tags)` calls (should be replaced with edge-weight-based similarity)
    - No direct calls to `api.anthropic.com`
    - No references to `e.tags` in any code path

11. **Console cleanup:** Remove any `console.log` debug statements added during S2/S3c (keep the null cluster_id warning).

12. **End-to-end smoke test:** The full user flow should work:
    - Load page → events and clusters fetched → strata view renders
    - Toggle to resonance → animated transition → constellation view
    - Click event node → event panel with participant color, note, archetype link
    - Click archetype name → archetype panel with myth text from backend
    - Click neighbor event → chained navigation to their event panel
    - Use participant toggle → opacity fade works
    - Close panel → clean state

## Constraints
- Do NOT modify: any backend files (`app/`, `scripts/`, `tests/`)
- Do NOT modify: the data fetching or rendering logic from S2 (only add participant color and toggle)
- Do NOT modify: the panel adaptation from S3c (only add participant color indicator)
- Do NOT add: new API endpoints or data sources
- Do NOT add: any features not in the Sprint 2 spec (no scroll/zoom, no mobile, no zamani view)

## Visual Review
The developer should visually verify:

1. **Participant colors on nodes:** Jessie events are purple (#7F77DD), Emma events are coral (#D85A30), Steven events are teal (#1D9E75). Colors visually distinct in both views.
2. **Edge colors unchanged:** Edges still use archetype cluster colors (not participant colors).
3. **Toggle UI:** Visible, properly styled in DM Mono, positioned without overlapping view toggle.
4. **Toggle "all":** All events at normal opacity.
5. **Toggle individual:** Selected participant's events bright, others faded to ~15%. Clear visual separation.
6. **Edge fading:** Edges between faded events also fade. Edges connecting to visible events partially visible.
7. **Toggle persistence:** Switch views while a participant is selected → filter persists in the new view.
8. **Event panel participant:** Shows participant name with colored dot, source type.
9. **End-to-end:** Full flow from page load to chained navigation to toggle, no errors.
10. **No mock data:** View page source — no hardcoded event arrays, no tag mappings.

Verification conditions:
- Events from at least 2 different participants in the database
- Test all 4 toggle states (all, jessie, emma, steven)
- Test toggle across view transitions

## Definition of Done
- [ ] Participant colors on event nodes matching design reference
- [ ] CSS variables for participant colors defined
- [ ] Toggle UI rendered with all/jessie/emma/steven buttons
- [ ] Opacity fade works for non-selected participants (~15%)
- [ ] Edge fade proportional to connected node visibility
- [ ] Toggle state persists across view transitions
- [ ] Event panel shows participant name with color indicator
- [ ] No hardcoded mock events remain anywhere in index.html
- [ ] No direct api.anthropic.com calls remain
- [ ] No console errors in full end-to-end flow
- [ ] All backend tests pass (full suite)
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| Both views render | Visual check |
| View transition works | Toggle strata↔resonance |
| Panels open and close | Click nodes and archetype names |
| Myth text loads | Open archetype panel, verify myth appears |
| Chained navigation works | Event → archetype → neighbor |
| Grain overlay visible | Visual check |
| Existing backend tests pass | `python -m pytest -x -q -n auto` |

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

**Write the close-out report to a file:**
docs/sprints/sprint-2/session-s4-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
Invoke the @reviewer subagent found at .claude/workflow/claude/agents/reviewer.md.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-2/review-context.md`
2. The close-out report path: `docs/sprints/sprint-2/session-s4-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest -x -q -n auto` (FINAL SESSION — full suite)
5. Files that should NOT have been modified: everything in `app/`, `tests/`, `scripts/`

The @reviewer will write its report to:
docs/sprints/sprint-2/session-s4-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS, follow the post-review fix documentation protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify participant colors match design reference exactly (jessie=#7F77DD, emma=#D85A30, steven=#1D9E75, shared=#BA7517)
2. Verify edge colors are still archetype-based (not participant-based)
3. Verify toggle fade is ~15% opacity (not 0%, not 50%)
4. Verify no hardcoded mock events remain (search for old event labels like "arrived", "first dinner here", "dream: corridor")
5. Verify no direct api.anthropic.com calls remain
6. Verify no `e.tags` references remain
7. Verify no `tagSim`, `primaryCluster(e.tags)`, or `allClusters(e.tags)` calls remain
8. Verify full backend test suite passes (this is the final session)

## Sprint-Level Regression Checklist (for @reviewer)
[Full checklist — this is the final session]
- [ ] All existing passing tests still pass (full suite with -n auto)
- [ ] GET /events returns correct data (additive only)
- [ ] GET /clusters returns correct data (additive only)
- [ ] POST /telegram processes and stores events
- [ ] POST /granola processes and stores events
- [ ] POST /myth returns myth text
- [ ] GET /health returns status
- [ ] Frontend served from / route
- [ ] Canvas-based rendering intact
- [ ] Both views render
- [ ] Animated transition functions
- [ ] Slide-out panel system works
- [ ] Chained navigation works
- [ ] Grain overlay visible
- [ ] Cormorant Garamond + DM Mono typography
- [ ] River-at-night color palette preserved
- [ ] Procfile unchanged
- [ ] No prohibited files modified (telegram.py, granola.py, embedding.py, init_supabase.sql, seed_clusters.py)

## Sprint-Level Escalation Criteria (for @reviewer)
- Any regression in backend tests → investigate immediately
- Canvas blank/broken → rendering regression from color changes
- Toggle breaks view transition → state management bug
- RSK-002: if myth text visible in panels contains therapy-speak → flag for prompt engineering
