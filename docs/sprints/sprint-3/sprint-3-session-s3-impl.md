# Sprint 3, Session S3: Myth Prompt Refinement

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/myth.py`
   - `tests/test_myth.py`
   - `docs/design-reference.md` (Copy Tone section)
2. Run scoped test baseline:
   ```
   python -m pytest tests/test_myth.py -x -q
   ```
   Expected: all passing (full suite confirmed by timestamp fix close-out)
3. Verify you are on the correct branch: `main`

## Sprint Context Update (from Work Journal)

**Current test baseline:** 144 passed, 3 skipped, 3 pre-existing errors (integration teardown FK constraint — ignore these)
**Hard floor:** ≥118 pass

The database now contains real seeded data from two Granola transcripts:
- March 17 transcript: 178 events (steven: 59, jessie: 35, emma: 84)
- March 18 transcript: 215 events (shared: 129, steven: 19, emma: 60, jessie: 7)
- Total: ~393 events across 6 seed clusters

**Cluster distribution from March 18 run:**
The Table: 102, The Hand: 38, What the Body Keeps: 25, The Silence: 24, The Root: 15, The Gate: 11

**Important context for myth quality testing:** Most events were assigned below the 0.3 cosine similarity threshold (typical range: 0.15–0.29). This is because seed cluster centroids were computed from tags, not from the embedding model. Events are loosely grouped — the myth prompt needs to work with semantically diffuse clusters, not tight ones. This makes the "embarrassment test" (could this sentence apply to anyone?) especially important.

Sessions completed before this one: S1a, S1b, S2, plus a timestamp fix prompt. All merged to main.

## Objective
Refine `build_myth_prompt` so myth output for real cluster data passes the Design Brief's tonal test ("marginalia in an old book"). Add thin-cluster handling for constellations with ≤2 events. Create a manual quality testing script.

## Requirements

1. **In `app/myth.py` — refine `build_myth_prompt`:**

   Replace the current prompt construction with a richer version. The prompt must include:

   a. **Expanded register instructions** (drawn from Design Brief Copy Tone section):
      - "You are speaking in an ancestral register. Ancestral and exact. A scholar who has spent years inside a subject, now speaking plainly about it to someone they respect."
      - "Not wellness. Not witchy. Not fantasy. Not therapy-speak. Not generic wisdom."
      - "If it sounds like a wellness app, discard it. If it sounds like a technical manual, discard it. If it sounds like marginalia in an old book, keep it."

   b. **Embarrassment test instruction:**
      - "This sentence could not have been written without these specific events. If it could apply to anyone's life, discard it and try again."

   c. **Event count context:**
      - Include the number of events: "This constellation holds {N} moments."

   d. **Thin-cluster handling:**
      When `len(event_labels) <= 2`, modify the prompt:
      - Reduce target sentence length: "Write one sentence (10–20 words)"
      - Add framing: "The constellation is still forming. Name the thread that is beginning to appear."
      When `len(event_labels) > 2`, keep the current target: "Write one sentence (20–35 words)" with full prompt.

   e. **Preserve existing elements:**
      - PROHIBITED_WORDS block must remain
      - PREFERRED_WORDS block must remain
      - "No quotation marks" instruction must remain
      - Cluster name and event labels block must remain

   The function signature stays the same: `build_myth_prompt(cluster_name: str, event_labels: list[str]) -> str`

2. **Create `scripts/test_myth_quality.py`:**

   A manual testing tool (NOT an automated test) that:
   - Connects to the production Supabase database
   - Fetches all clusters that have events (event_count > 0)
   - For each cluster: fetches event labels, calls `generate_myth`, prints:
     ```
     === The Gate (12 events) ===
     Events: "dreamed about crossing...", "the door that appeared...", ...
     Myth: "What the gate remembers is not the leaving but the leaning toward."
     ---
     ```
   - At the end, prints a summary: total clusters, clusters with myths, any errors

   Usage:
   ```
   python -m scripts.test_myth_quality
   ```

   This script requires live API keys (ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY) in the environment. It should load from `.env` via `dotenv`.

## Constraints
- Do NOT modify: `app/db.py`, `app/clustering.py`, `app/telegram.py`, `app/granola.py`, `app/config.py`, `app/models.py`, `app/embedding.py`, `app/main.py`, `static/index.html`
- Do NOT change: `should_regenerate`, `generate_myth`, `get_or_generate_myth` function logic (only `build_myth_prompt` changes)
- Do NOT change: the `PROHIBITED_WORDS` or `PREFERRED_WORDS` constants (content may be adjusted if needed, but the enforcement pattern must remain)
- Do NOT change: the myth caching mechanism (version, delta-based regeneration)
- Do NOT add: new API endpoints

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write:
  1. `test_build_myth_prompt_includes_register_guidance` — verify the prompt string contains "ancestral" and "marginalia" (key register terms)
  2. `test_build_myth_prompt_thin_cluster` — with event_labels of length 1, verify prompt contains "still forming" and shorter word count target
  3. `test_build_myth_prompt_normal_cluster` — with event_labels of length 5, verify prompt contains "20-35 words" target
- Minimum new test count: 3
- Test command: `python -m pytest -n auto -q`

## Definition of Done
- [x] `build_myth_prompt` includes expanded register instructions
- [x] `build_myth_prompt` includes embarrassment test instruction
- [x] `build_myth_prompt` includes event count context
- [x] Thin-cluster variant triggers at len(event_labels) ≤ 2
- [x] PROHIBITED_WORDS and PREFERRED_WORDS still present
- [x] `scripts/test_myth_quality.py` exists and can be run manually
- [x] All existing tests pass
- [x] 3 new tests written and passing
- [x] Close-out report written to file
- [x] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| `should_regenerate` logic unchanged | Existing myth tests pass |
| `generate_myth` fallback on error unchanged | Existing myth tests pass |
| `get_or_generate_myth` caching logic unchanged | Existing myth tests pass |
| PROHIBITED_WORDS constant still present | `grep "PROHIBITED_WORDS" app/myth.py` |
| Function signature unchanged | `build_myth_prompt(cluster_name: str, event_labels: list[str]) -> str` |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-3/session-s3-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3/session-s3-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (scoped): `python -m pytest tests/test_myth.py -x -q`
5. Files that should NOT have been modified: `app/db.py`, `app/clustering.py`, `app/telegram.py`, `app/granola.py`, `app/config.py`, `app/models.py`, `app/embedding.py`, `app/main.py`, `static/index.html`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3/session-s3-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the standard protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify `build_myth_prompt` includes the key register terms: "ancestral", "marginalia", "scholar"
2. Verify thin-cluster path triggers at ≤2 events with shorter word target and "still forming" framing
3. Verify PROHIBITED_WORDS and PREFERRED_WORDS are still enforced in the prompt
4. Verify `should_regenerate`, `generate_myth`, and `get_or_generate_myth` are NOT modified
5. Verify the myth caching logic (version, delta) is completely untouched
6. Read the prompt output for a sample cluster and assess: does it sound like marginalia in an old book, or wellness?

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Current: 144 passed, 3 skipped, 3 pre-existing errors
- Hard floor: ≥118 pass

### Critical Invariants
- Myth caching mechanism unchanged
- All other app/ modules unchanged
- All API endpoint contracts unchanged

## Sprint-Level Escalation Criteria
1. Myth output consistently fails tonal test after 3+ prompt iterations → escalate
2. Test pass count drops below 118 → investigate
3. Changes needed to `generate_myth` or `get_or_generate_myth` → escalate (prompt-only changes in scope)