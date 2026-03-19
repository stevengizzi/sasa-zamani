# Sprint 3, Session S4: Frontend Demo Polish

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `static/index.html` (the entire frontend — scan for: panel open/close functions, event click handlers, archetype click handlers, participant toggle handler, data fetch calls, and the strata view time-axis rendering code)
   - `docs/design-reference.md` (Copy Tone section for loading state text)
2. Run scoped test baseline:
   ```
   python -m pytest tests/test_endpoints.py -x -q
   ```
   Expected: all passing
3. Verify you are on the correct branch: `main`

## Sprint Context Update (from Work Journal)

**Current test baseline:** 144 passed, 3 skipped, 3 pre-existing errors (integration teardown FK constraint — ignore these)
**Hard floor:** ≥118 pass

The database now contains real seeded data from two Granola transcripts:
- March 17 transcript: 178 events (event_date = 2026-03-17)
- March 18 transcript: 215 events (event_date = 2026-03-18)
- Total: ~393 events across 6 seed clusters, 3 participants + shared

**Critical frontend issue discovered during sprint:** The strata view time axis currently plots events using `created_at` (the Supabase insert timestamp). All seeded events were inserted today (March 19), so they pile at a single point on the time axis despite having different `event_date` values. Requirement 5 below addresses this — it is the highest-priority item in this session.

Sessions completed before this one: S1a, S1b, S2, timestamp fix, and S3 (running in parallel). All prior sessions merged to main.

**Note:** S3 (myth prompt refinement) may be running in parallel in a separate Claude Code session. S3 modifies `app/myth.py` and creates `scripts/test_myth_quality.py`. There is NO file overlap with S4 — S4 only touches `static/index.html`. However, coordinate git commits if both sessions finish around the same time.

## Objective
Add five frontend improvements for demo readiness: strata view time axis fix, Esc key to close panels, archetype→event reverse chaining, smooth fade animation on participant toggle, and a loading state for initial data fetch.

## Requirements

1. **Esc key to close panels:**
   Add a `document.addEventListener('keydown', ...)` handler. When `event.key === 'Escape'`, close any open slide-out panel by calling the existing panel-close function. If no panel is open, the keypress should be a no-op (no errors). This should work regardless of which panel type is open (event detail or archetype detail).

2. **Archetype→event reverse chaining:**
   In the archetype detail panel rendering code, event labels/names are currently displayed as text. Make them clickable. When a user clicks an event name in the archetype detail panel:
   - Close the archetype detail panel
   - Open the event detail panel for that specific event
   - The event object must be found from the fetched events array (match by event ID if available in the panel data, or by label as fallback)

   This completes the chained navigation cycle: event panel → archetype panel → event panel.

3. **Smooth fade animation on participant toggle:**
   Find the participant toggle handler. Currently, when a participant is selected/deselected, non-matching events change opacity instantly (snap). Replace this with a smooth transition:
   - If opacity is applied via Canvas drawing: implement a short animation loop (300ms duration) that interpolates opacity from current to target value, redrawing each frame via `requestAnimationFrame`
   - If opacity is applied via CSS/DOM: add `transition: opacity 0.3s ease` to the relevant elements
   - The toggle itself should feel responsive — the click registers immediately, the visual fade follows

4. **Loading state for initial data fetch:**
   Before `/events` and `/clusters` responses arrive, the canvas area is empty. Add a loading indicator:
   - Display centered text: "The pattern is still forming..." (Design Brief empty-state language)
   - Use the existing page font at a size that reads comfortably
   - Remove the loading text once data arrives and the first render completes
   - If data fetch fails, show: "Something unexpected was encountered." (Design Brief error-state language)

5. **Strata view: use `event_date` for time axis (HIGHEST PRIORITY):**
   The strata view plots events on the Y-axis by time. Currently it reads `created_at` from event data. Change this to prefer `event_date` when present, falling back to `created_at` when `event_date` is null or absent.

   The logic should be: `event.event_date || event.created_at`

   This ensures seeded transcript events (which have `event_date` set to the original transcript date) appear at the correct position on the time axis, rather than all piling at the insert timestamp.

   The `/events` endpoint already returns both `created_at` and `event_date` fields. No backend changes needed.

## Constraints
- Do NOT modify: any `app/` files, any `tests/` files, any `scripts/` files, any `docs/` files
- Do NOT change: the data fetch logic (URLs, parsing, error handling for the API calls themselves)
- Do NOT change: the Canvas rendering logic for node positioning, view transitions, or color encoding (except the time-axis data source change in requirement 5)
- Do NOT add: new JavaScript dependencies or external libraries
- Do NOT refactor: the single-file architecture. All changes go in `static/index.html`.
- Keep changes minimal and surgical. The 48K file is fragile — test every interaction after each change.

## Visual Review
The developer should visually verify the following after this session:

1. **Strata view time axis:** Events should appear at two distinct time positions (March 17 and March 18), NOT all piled at March 19. This is the most important visual check.
2. **Esc key:** Open an event detail panel → press Esc → panel closes. Open an archetype detail panel → press Esc → panel closes. Press Esc with no panel open → nothing happens (no console errors).
3. **Reverse chaining:** Click an event node → event panel opens → click archetype name → archetype panel opens → click an event name in the archetype panel → event panel opens for that event. Full cycle works.
4. **Fade animation:** Click a participant in the toggle → non-matching events fade smoothly (not snap) to reduced opacity over ~300ms. Click "all" → events fade back to full opacity smoothly.
5. **Loading state:** Hard refresh the page → "The pattern is still forming..." appears briefly → replaced by the map once data loads. (Test with DevTools Network throttling set to "Slow 3G" for a clearer view of the loading state.)

Verification conditions:
- Production URL loaded in Chrome with DevTools open (Console tab for errors)
- Seeded data present (~393 events across 6 clusters)
- Both strata and resonance views tested

## Test Targets
No automated tests (Canvas-based single-file frontend). All verification is visual per the Visual Review section above.

## Definition of Done
- [x] Strata view plots events by `event_date` (falling back to `created_at`)
- [x] Esc key closes any open panel
- [x] Clicking event name in archetype panel opens that event's detail panel
- [x] Participant toggle opacity change animates smoothly (~300ms)
- [x] Loading state text appears before data loads
- [x] All existing interactions still work (both views, transition, panels, toggle, chained navigation)
- [x] No console errors in browser DevTools
- [x] Close-out report written to file
- [x] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| Both views render correctly | Visual check — strata and resonance views |
| Strata view shows events at two dates | Events at Mar 17 and Mar 18, not Mar 19 |
| View transition animates | Click the view toggle, verify animation |
| Event click → event panel | Click an event node |
| Archetype click → archetype panel | Click archetype name in event panel |
| Panel close button still works | Click the X/close button |
| Participant toggle works | Click each participant name |
| Color encoding correct | jessie=purple, emma=coral, steven=teal, shared=gold |
| No console errors | Check DevTools Console tab |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-3/session-s4-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3/session-s4-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest -n auto -q` (final session before verification — full suite)
5. Files that should NOT have been modified: all `app/` files, all `tests/` files, all `scripts/` files

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3/session-s4-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the standard protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify NO `app/`, `tests/`, or `scripts/` files were modified
2. Verify the strata view time axis reads `event_date` with fallback to `created_at`
3. Check that the Esc handler doesn't interfere with text input fields (if any exist)
4. Check that reverse chaining correctly identifies the event (by ID, not just by label substring match which could be ambiguous)
5. Check that the fade animation doesn't cause visual artifacts or flicker during the transition
6. Check that the loading state is removed (not just hidden behind the canvas) after data loads
7. Review for any new global variables or event listeners that could leak or conflict

## Visual Review (for @reviewer)
The reviewer should visually verify (or ask the developer to verify):
1. Strata view shows events at two time positions (Mar 17, Mar 18)
2. Esc key closes panels (both types, no error when no panel open)
3. Full chained navigation cycle: event → archetype → event (reverse chain)
4. Participant toggle fades smoothly (~300ms, not instant)
5. Loading state appears on hard refresh, disappears when data loads

Verification conditions:
- Production URL in Chrome with DevTools Console open
- Network throttling to "Slow 3G" for loading state test

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Current: 144 passed, 3 skipped, 3 pre-existing errors
- Hard floor: ≥118 pass

### Critical Invariants
- All backend tests pass (no app/ files touched)
- Frontend: both views, transition, panels, toggle, chained navigation, color encoding

## Sprint-Level Escalation Criteria
1. Frontend changes break existing interactions → stop and escalate
2. Test pass count drops below 118 → investigate