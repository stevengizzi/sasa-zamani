# Sprint 4, Session 3: Archetype Creation Core

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/clustering.py`
   - `app/config.py`
   - `app/db.py` (insert_cluster, get_cluster_by_id, get_cluster_events_labels)
   - `docs/design-reference.md` (Copy Tone section)
   - `docs/sprints/sprint-4/sprint-spec.md`
2. Run scoped test baseline:
   `python -m pytest tests/test_clustering.py -x -q`
   Expected: all passing
3. Verify you are on branch: `sprint-4`

## Objective
Build the below-threshold cluster creation path (implementing DEC-011's designed-but-unbuilt feature) and the deferred archetype naming module.

## Requirements

1. In `app/config.py`, add to Settings:
   - `archetype_naming_threshold: int = 3`

2. In `app/clustering.py`, add function:
   ```python
   def assign_or_create_cluster(
       embedding: list[float],
       centroids: list[tuple[str, list[float]]],
   ) -> tuple[str, float, bool]:
       """Assign an embedding to the nearest cluster, or create a new one if below threshold.

       Returns (cluster_id, similarity_score, created).
       - If best similarity >= threshold: returns (best_cluster_id, score, False)
       - If best similarity < threshold: creates a new cluster and returns (new_id, score, True)
       """
   ```
   Implementation:
   - Reuse the existing similarity computation logic from assign_cluster()
   - When below threshold, call `create_dynamic_cluster(embedding)`
   - The existing `assign_cluster()` function must remain unchanged for backward compatibility

3. In `app/clustering.py`, add function:
   ```python
   def create_dynamic_cluster(centroid_embedding: list[float]) -> str:
       """Create a new dynamic cluster with placeholder name. Returns the new cluster ID."""
   ```
   Implementation:
   - Call `insert_cluster(name="The Unnamed", centroid_embedding=centroid_embedding, is_seed=False, glyph_id=None)`
   - Return the new cluster's ID
   - Log: "Created new dynamic cluster {id}"

4. Create `app/archetype_naming.py`:
   - Define `ARCHETYPE_NAMING_PROMPT`:
     ```
     You are naming a constellation of related events. Given the event labels and
     their content below, propose an archetype name.

     Rules:
     - The name should follow the pattern "The [Noun]" or a short noun-phrase
     - Write in the register of a scholar's margin note: precise, ancestral, not vague
     - Never use: journey, transformation, growth, powerful, explore, reflect,
       synchronicity, discover, reveal, activation
     - The name should feel found rather than made — as if it already existed and
       you are recognizing it
     - Return ONLY the archetype name, nothing else

     Event labels:
     {labels}

     Event content (excerpts):
     {notes}
     ```
   - Function: `generate_archetype_name(event_labels: list[str], event_notes: list[str]) -> str`
     - Calls Claude (claude-sonnet-4-20250514) with the naming prompt
     - Returns the generated name string
     - Raises `ArchetypeNamingError` on API failure
   - Function: `maybe_name_cluster(cluster_id: str) -> str | None`
     - Fetches cluster by ID. If name != "The Unnamed", return None (already named).
     - Fetches cluster event count. If < archetype_naming_threshold, return None (not enough events).
     - Fetches event labels and notes for the cluster.
     - Calls generate_archetype_name().
     - Updates cluster name in DB.
     - Returns the new name.
     - On naming API failure: log error, return None (keep "The Unnamed").
   - Exception class: `ArchetypeNamingError`

5. In `app/db.py`, add function (if not already present):
   ```python
   def update_cluster_name(cluster_id: str, name: str) -> None:
       """Update a cluster's name."""
   ```

6. In `app/db.py`, add function:
   ```python
   def get_cluster_events_notes(cluster_id: str) -> list[str]:
       """Return event notes (first 200 chars each) for a cluster."""
   ```

## Constraints
- Do NOT modify: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/segmentation.py`, `app/granola.py`, `app/telegram.py`
- Do NOT change: `assign_cluster()` function — it must remain unchanged for backward compatibility
- Do NOT add: New API endpoints
- The archetype naming prompt MUST follow the Copy Tone rules from design-reference.md (the "Never use these words" list is explicitly in the prompt)

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests:
  - In `tests/test_clustering.py`:
    1. assign_or_create_cluster above threshold returns (id, score, False)
    2. assign_or_create_cluster below threshold returns (new_id, score, True)
    3. assign_or_create_cluster at exactly threshold returns (id, score, False)
    4. create_dynamic_cluster inserts cluster with name="The Unnamed", is_seed=False
    5. assign_cluster still works unchanged (backward compat)
  - In `tests/test_archetype_naming.py` (new file):
    6. generate_archetype_name returns a string
    7. generate_archetype_name prompt includes prohibited words list
    8. maybe_name_cluster names when event_count >= threshold and name is "The Unnamed"
    9. maybe_name_cluster no-op when event_count < threshold
    10. maybe_name_cluster no-op when name already set
    11. maybe_name_cluster handles API failure gracefully (returns None)
  - In `tests/test_db.py`:
    12. update_cluster_name updates correctly
    13. get_cluster_events_notes returns truncated notes
- Minimum new test count: 10
- Test command: `python -m pytest tests/test_clustering.py tests/test_archetype_naming.py tests/test_db.py -x -q`

## Config Validation
Verify that `archetype_naming_threshold` is accessible via `get_settings().archetype_naming_threshold` and defaults to 3.

## Definition of Done
- [ ] All requirements implemented
- [ ] All existing tests pass
- [ ] ≥10 new tests written and passing
- [ ] Config field accessible with correct default
- [ ] assign_cluster() backward compatible
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| assign_cluster unchanged | Existing test_clustering.py tests pass unchanged |
| insert_cluster works for dynamic | New test for create_dynamic_cluster |
| compute_xs handles unknown cluster names | XS_CENTERS.get() returns _DEFAULT_XS_CENTER for new names |

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-4/session-3-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer subagent.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-4/review-context.md`
2. The close-out report path: `docs/sprints/sprint-4/session-3-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_clustering.py tests/test_archetype_naming.py tests/test_db.py -x -q`
5. Files that should NOT have been modified: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/segmentation.py`, `app/granola.py`, `app/telegram.py`

The @reviewer will write its report to: docs/sprints/sprint-4/session-3-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the implementation
prompt template instructions.

## Session-Specific Review Focus (for @reviewer)
1. Verify assign_cluster() is truly unchanged (diff should show no modifications to existing function)
2. Verify the archetype naming prompt contains all PROHIBITED words from design-reference.md
3. Verify maybe_name_cluster checks BOTH conditions (event_count AND name == "The Unnamed")
4. Verify create_dynamic_cluster sets is_seed=False
5. Verify maybe_name_cluster failure path does not raise — returns None and logs

## Sprint-Level Regression Checklist
- [ ] All 166 pre-Sprint 4 tests pass
- [ ] assign_cluster() unchanged
- [ ] compute_xs() works for new cluster names (default center)
- [ ] increment_event_count() works for dynamic clusters
- [ ] New config fields have defaults

## Sprint-Level Escalation Criteria
1. Archetype names fail Copy Tone test at ≥50% → escalate for prompt redesign
