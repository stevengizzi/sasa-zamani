# Sprint 2, Session S3a: Myth Module + Tests

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/myth.py` (currently a 1-line stub)
   - `app/db.py` (for cluster/event/myth query functions)
   - `app/config.py` (for Settings model)
   - `app/models.py` (for response models)
   - `docs/sprints/sprint-2/sprint-spec.md` (acceptance criteria for deliverable 3)
   - `docs/design-reference.md` (copy tone section — "never use" words list)
2. Run the test baseline:
   Scoped: `python -m pytest tests/test_clustering.py tests/test_db.py tests/test_endpoints.py -x -q`
   Expected: all passing (full suite confirmed by S1 close-out)
3. Verify you are on the correct branch

## Objective
Implement the myth generation module — prompt construction in the ancestral register, Claude API call, cache logic against the myths table, and regeneration trigger based on event count delta.

## Requirements

1. **In `app/config.py`:** Add `anthropic_api_key: str` to the `Settings` class. This maps to the `ANTHROPIC_API_KEY` environment variable.

2. **In `app/myth.py`:** Replace the 1-line stub with a complete module containing:

   a. **`build_myth_prompt(cluster_name: str, event_labels: list[str]) -> str`**
      - Constructs a prompt for Claude in the ancestral register
      - Includes the archetype name and the list of event labels in the cluster
      - Prompt instructions specify: "not explanation, not analysis. Short, poetic, oracular."
      - Prompt specifies: "Write one sentence (20-35 words) in an ancestral register that names what this cluster is actually about — what thread runs through all these moments. Speak as if from the past looking forward. No quotation marks."
      - Prompt includes prohibited words from the design reference: detect, discover, reveal, collective unconscious, synchronicity, universe, field, activation, signal, journey, transformation, powerful, growth, explore, reflect
      - Prompt includes preferred words as guidance: scaffold, propose, candidate, resonate, vessel, compost, harvest window, rhyme, constellation, intersubjective, meaning-making, narrative commons

   b. **`should_regenerate(cluster_id: str, current_event_count: int) -> bool`**
      - Queries the myths table for the most recent myth for this cluster
      - Returns True if no myth exists
      - Returns True if `current_event_count - event_count_at_generation >= 3`
      - Returns False otherwise

   c. **`generate_myth(cluster_id: str, cluster_name: str, event_labels: list[str]) -> str`**
      - Calls `build_myth_prompt` to construct the prompt
      - Calls the Anthropic API (Claude claude-sonnet-4-20250514) with max_tokens=100
      - Parses the response to extract the text content
      - On API error or empty response, returns "The pattern holds."
      - Does NOT handle caching — that's the caller's responsibility

   d. **`get_or_generate_myth(cluster_id: str) -> tuple[str, bool]`**
      - Top-level function called by the endpoint
      - Fetches cluster data (name, event_count) and event labels from the database
      - Checks for cached myth in the myths table
      - If cached and `should_regenerate` returns False: return (cached_text, True)
      - If no cache or stale: call `generate_myth`, store result in myths table with version tracking, update cluster myth_text, return (new_text, False)
      - Returns tuple of (myth_text, is_cached)

3. **Database queries needed** (add to `app/db.py` if not already present):
   - `get_latest_myth(cluster_id: str) -> dict | None` — most recent myth entry for a cluster
   - `insert_myth(cluster_id: str, text: str, event_count: int, version: int) -> dict` — new myth entry
   - `update_cluster_myth(cluster_id: str, myth_text: str) -> None` — update cluster's myth_text field
   - `get_cluster_events_labels(cluster_id: str) -> list[str]` — return event labels for a cluster
   - `get_cluster_by_id(cluster_id: str) -> dict | None` — return a single cluster by ID

## Constraints
- Do NOT modify: `app/telegram.py`, `app/granola.py`, `app/embedding.py`, `app/main.py` (endpoint wiring is S3b), `static/index.html`
- Do NOT change: any existing database query functions in `db.py` (only add new ones)
- Do NOT add: any API endpoints (that's S3b)
- The Anthropic SDK should be imported from the `anthropic` package. Verify it's in `requirements.txt` — if not, add it.
- Use `get_settings().anthropic_api_key` for the API key, not os.environ directly.

## Config Validation
Write a test that verifies the `anthropic_api_key` field is recognized by the `Settings` model:
1. Create a `Settings` instance with all required fields including `anthropic_api_key`
2. Verify the field is accessible and has the expected value
3. Verify that `Settings.model_fields` contains `anthropic_api_key`

Expected mapping:
| Env Var | Model Field |
|---------|-------------|
| ANTHROPIC_API_KEY | anthropic_api_key |

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write:
  1. `build_myth_prompt` includes cluster name in output
  2. `build_myth_prompt` includes event labels in output
  3. `build_myth_prompt` includes ancestral register instruction
  4. `build_myth_prompt` includes at least some prohibited words in the prohibition list
  5. `should_regenerate` returns True when no myth exists (mocked DB returning None)
  6. `should_regenerate` returns True when event_count delta >= 3 (mocked)
  7. `should_regenerate` returns False when event_count delta < 3 (mocked)
  8. `generate_myth` returns text from mocked Claude response
  9. `generate_myth` returns "The pattern holds." on mocked API error
  10. Config validation: `anthropic_api_key` recognized by Settings model
- Minimum new test count: 6
- Test file: `tests/test_myth.py` (new file)
- Test command: `python -m pytest tests/test_myth.py -x -q`

## Definition of Done
- [ ] `app/myth.py` fully implemented (build_myth_prompt, should_regenerate, generate_myth, get_or_generate_myth)
- [ ] `app/config.py` has anthropic_api_key field
- [ ] `anthropic` in requirements.txt
- [ ] New DB query functions added to `app/db.py`
- [ ] All existing tests pass
- [ ] 6+ new tests written and passing in `tests/test_myth.py`
- [ ] Config validation test passing
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| Existing Settings fields still work | Existing tests that use get_settings() pass |
| Existing DB functions unchanged | test_db.py passes |
| No new API endpoints added | grep for @app in main.py — count unchanged |
| myth.py stub replaced, not duplicated | Only one app/myth.py exists |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-2/session-s3a-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-2/review-context.md`
2. The close-out report path: `docs/sprints/sprint-2/session-s3a-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_myth.py -x -q`
5. Files that should NOT have been modified: `app/telegram.py`, `app/granola.py`, `app/embedding.py`, `app/main.py`, `static/index.html`

The @reviewer will write its report to:
docs/sprints/sprint-2/session-s3a-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS, follow the post-review fix documentation protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify myth prompt includes the ancestral register instruction and prohibited words list
2. Verify `should_regenerate` checks event_count delta of 3 (not some other number)
3. Verify `generate_myth` graceful failure returns exactly "The pattern holds." (not a variant)
4. Verify Anthropic SDK is used with `get_settings().anthropic_api_key` (not hardcoded key, not os.environ)
5. Verify no new endpoints were added to main.py
6. Verify myth version tracking: new myths get version = previous version + 1
7. Verify `anthropic` package is in requirements.txt

## Sprint-Level Regression Checklist (for @reviewer)
- [ ] All existing passing tests still pass
- [ ] Existing config fields unchanged
- [ ] No prohibited files modified
- [ ] No new API endpoints added (that's S3b)

## Sprint-Level Escalation Criteria (for @reviewer)
- 5+ existing tests fail → stop and assess
- Myth prompt produces therapy-speak in test outputs → RSK-002 flag
