# Sprint 2, Session S2f: Visual Review Fixes — Panel/Toggle Interaction Bugs

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `static/index.html` (the entire frontend — focus on panel open/close logic and view toggle logic)
   - `docs/sprints/sprint-2/session-s2-closeout.md` (S2 implementation context)
2. Run the test baseline:
   Full suite: `python -m pytest -x -q`
   Expected: 118 passed, 3 skipped, 0 failed
3. Verify you are on the correct branch
4. Open the deployed site and reproduce both bugs before writing any code

## Objective
Fix two interaction bugs discovered during the S2 visual review. Both involve the slide-out panel interfering with other UI systems.

## Bug 1: View toggle breaks when slide-out panel is open

**Reproduction:**
1. Load the page in Resonance view (or toggle to Resonance)
2. Click any event node or archetype name to open the slide-out panel
3. While the panel is open, click the "strata" toggle button
4. **Expected:** View transitions to Strata, panel can remain open or close
5. **Actual:** Nothing happens. The view stays in Resonance. Clicking the toggle button has no effect. Page refresh is required to recover.

**Likely cause:** The panel open state is blocking or consuming the toggle click event, or the toggle handler has a guard condition that evaluates false when a panel is open (e.g., checking an animation state that the panel transition has put into a stuck value).

**Fix approach:** The view toggle must work regardless of panel state. Either close the panel when the view toggles, or allow both to coexist. Closing the panel on view toggle is the safer option — the panel content references spatial positions that change between views.

## Bug 2: Chained panel navigation closes panel instead of transitioning

**Reproduction:**
1. Open the slide-out panel by clicking an event node
2. In the event panel, click the archetype name link (e.g., "The Gate") which should navigate to that archetype's panel
3. **Expected:** The panel content transitions to show the archetype panel (chained navigation — this is a core interaction from the prototype)
4. **Actual:** The panel briefly flashes the archetype content then closes entirely. The user sees a brief flash of the target panel before it disappears.

**Likely cause:** The panel navigation triggers both a "show new panel" and a "close panel" action. Likely the click handler on the link is opening the new panel AND the click is also propagating to a backdrop/overlay close handler, or the archetype click handler calls the same function that toggles panel visibility (open if closed, close if open — and since a panel is already open, it closes).

**Fix approach:** Panel-internal navigation links should replace panel content, not toggle panel visibility. When a link inside an open panel targets another panel, it should swap the content without closing and reopening. If the implementation uses a toggle pattern, internal links need to call "open specific panel" not "toggle panel."

## Constraints
- ONLY modify: `static/index.html`
- Do NOT modify: any backend files (`app/`, `tests/`, `scripts/`)
- Do NOT change: CSS styles (lines 1-179 of index.html)
- Do NOT change: HTML structure (panel divs, toggle buttons, grain overlay)
- Do NOT change: canvas rendering logic (node drawing, edge drawing, transition animation math)
- Do NOT change: data fetching or data transformation logic
- Changes must be limited to event handler wiring, panel open/close logic, and toggle interaction logic

## Test Approach
No new pytest tests (frontend-only session). Verification is manual:

### Bug 1 verification:
- [ ] Open panel in Strata view → click "resonance" toggle → view transitions correctly
- [ ] Open panel in Resonance view → click "strata" toggle → view transitions correctly
- [ ] Toggle works without panel open (regression check)
- [ ] After toggling with panel open, the next panel open still works correctly

### Bug 2 verification:
- [ ] Click event node → event panel opens → click archetype name → archetype panel appears (no flash, no close)
- [ ] Click archetype name in map → archetype panel opens → click event name in the event list → event panel appears
- [ ] Panel close button (or clicking outside) still closes the panel
- [ ] Clicking the same panel link that's already showing doesn't break anything

### Regression checks:
- [ ] Both Strata and Resonance views render correctly
- [ ] Animated transition between views works
- [ ] Node hover still shows event labels
- [ ] Grain overlay visible
- [ ] Axis labels visible
- [ ] Empty state still works (if all events are removed)
- [ ] All backend tests still pass: `python -m pytest -x -q`

## Definition of Done
- [ ] Bug 1 fixed: view toggle works regardless of panel state
- [ ] Bug 2 fixed: panel-internal links transition content without closing
- [ ] All manual verification checks above pass
- [ ] All backend tests pass (no regressions)
- [ ] Close-out report written to file

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-2/session-s2f-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-2/review-context.md`
2. The close-out report path: `docs/sprints/sprint-2/session-s2f-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest -x -q`
5. Files that should NOT have been modified: everything in `app/`, `tests/`, `scripts/`

The @reviewer will write its report to:
docs/sprints/sprint-2/session-s2f-review.md

## Session-Specific Review Focus (for @reviewer)
1. Verify Bug 1 fix: identify the specific code change that allows toggle while panel is open
2. Verify Bug 2 fix: identify the specific code change that prevents panel close during internal navigation
3. Verify no canvas rendering logic was modified
4. Verify no data fetching logic was modified
5. Verify CSS and HTML structure unchanged

## Sprint-Level Regression Checklist (for @reviewer)
- [ ] All backend tests still pass
- [ ] No backend files modified
- [ ] CSS styles unchanged
- [ ] HTML structure unchanged
- [ ] Both views render
- [ ] Transition animation works