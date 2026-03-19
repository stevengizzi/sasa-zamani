# Sprint 2, Fix Session: Toggle Permanently Broken After Panel Open

## Context
This is a **targeted fix** for a bug that survived the S2f fix session. The S2f fix added `closePanelFull()` before view toggle, which was based on an incorrect assumption that the panel being open was blocking the toggle. The actual symptom is more severe: **the toggle is permanently dead after the first panel open, even after the panel is closed.**

## Pre-Flight Checks
1. Read `static/index.html` — focus on:
   - The toggle button click handlers (`btn-strata`, `btn-resonance`)
   - The `openPanel()` / `closePanel()` / `closePanelFull()` functions
   - How event listeners are attached to the toggle buttons
   - Any global state variables that gate toggle behavior
2. **Reproduce the bug before writing any code:**
   - Load the page with data present
   - Verify both toggle buttons work (Strata ↔ Resonance)
   - Open any panel (click a node or archetype name)
   - Close the panel
   - Try both toggle buttons — they should be dead. Neither direction works.
   - This confirms the bug. Do not proceed until you've reproduced it.

## Bug Description
**Symptom:** After opening a slide-out panel for the first time, the Strata/Resonance toggle buttons stop working permanently. Closing the panel does not restore them. Both directions are affected. The only recovery is a page refresh.

**Key constraint:** The S2f fix (closePanelFull before toggle) is already in place and did not resolve this. The root cause is NOT the panel being open at the time of toggle. Something that happens during the first panel open permanently breaks the toggle and is never restored.

## Diagnostic Instructions
Before writing any fix, investigate and document the root cause. Check these hypotheses in order:

### Hypothesis A: innerHTML replacement destroys toggle button listeners
`openPanel()` uses innerHTML replacement. If the toggle buttons (`btn-strata`, `btn-resonance`) are inside a container whose innerHTML gets replaced or are re-queried after replacement in a way that creates new elements, the original event listeners would be orphaned.

**Check:** Are the toggle buttons inside or siblings of the panel container? Does any innerHTML replacement affect the DOM subtree containing the toggle buttons? After `openPanel()` runs, do `document.getElementById('btn-strata')` and `document.getElementById('btn-resonance')` still reference the same DOM nodes that have listeners attached?

### Hypothesis B: Global state variable set on panel open, never cleared
A flag or state variable (e.g., `panelOpen`, `animating`, `transitioning`) could be set to true during panel open and either not cleared on close, or cleared but checked in a way that still blocks the toggle.

**Check:** Trace every variable that the toggle click handlers read. After opening and closing a panel, are all of those variables in the same state as before the panel was opened?

### Hypothesis C: Animation state corruption
The panel open/close might interfere with `transDir` or `transProgress` values that the toggle handler checks before allowing a view switch.

**Check:** Log the values of `transDir`, `transProgress`, `panelOpen`, and any other state the toggle handler checks — log them both before and after a panel open/close cycle.

### Hypothesis D: Event listener re-registration
If toggle button listeners are attached inside a function that also gets called during panel setup, they might be re-attached to new/different elements or with different closures that capture stale state.

**Check:** Search for all places where `btn-strata` and `btn-resonance` get `addEventListener` calls. Is it only once at init, or could it happen again during panel operations?

## Fix Requirements
1. **Document the root cause** in the close-out before describing the fix
2. The fix must make both toggle buttons work at all times — before any panel open, during panel open, after panel close, after multiple panel open/close cycles
3. Do NOT rewrite the toggle or panel systems. Make the minimum targeted change.
4. Do NOT change CSS, HTML structure, canvas rendering, or data fetching logic
5. Only modify `static/index.html`

## Verification
After fixing, run through this exact sequence twice:
1. Load page → verify both toggles work
2. Open event panel → close panel → verify both toggles work
3. Open archetype panel → close panel → verify both toggles work
4. Open panel → toggle view (panel should close, view should switch) → verify toggle still works
5. Open panel → use chained navigation → close panel → verify both toggles work
6. Run `python -m pytest -x -q` to confirm no backend regressions

## Constraints
- ONLY modify: `static/index.html`
- Do NOT modify: any file in `app/`, `tests/`, `scripts/`
- Do NOT change: CSS styles, HTML structure, canvas rendering logic, data fetching logic

## Close-Out
Write the close-out report to:
`docs/sprints/sprint-2/session-s2f2-closeout.md`

The close-out MUST include:
- The confirmed root cause (which hypothesis, or a new one)
- The specific code change and why it fixes the root cause
- Structured JSON appendix fenced with ```json:structured-closeout

## Tier 2 Review (Mandatory — @reviewer Subagent)
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-2/review-context.md`
2. The close-out report path: `docs/sprints/sprint-2/session-s2f2-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest -x -q`
5. Files that should NOT have been modified: everything in `app/`, `tests/`, `scripts/`

The @reviewer will write its report to:
`docs/sprints/sprint-2/session-s2f2-review.md`

## Session-Specific Review Focus (for @reviewer)
1. Verify the documented root cause matches the code change
2. Verify the fix is minimal and targeted — not a rewrite
3. Verify no canvas rendering logic was modified
4. Verify no data fetching logic was modified
5. Verify CSS and HTML structure unchanged
6. Verify the toggle works in the verification sequence described above