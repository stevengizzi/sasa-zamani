# Sprint 3.5, Fix Session F1: Segmentation max_tokens and client timeout

## Context
This is a targeted fix session for a scope gap discovered during S3 (re-seed).

**Original session:** S1a (created `app/segmentation.py`)
**Issue type:** Category 3 — Scope Gap (small)
**Issue description:** `segment_transcript()` uses `max_tokens=4096`, which truncates the Claude API response when processing large transcripts. The March 17 transcript (~80K chars ≈ 20K tokens) and March 18 transcript (~136K chars ≈ 34K tokens) both exceed this limit because the prompt instructs Claude to return verbatim segment text in JSON. Additionally, the Anthropic client has no explicit timeout, causing the SDK's auto-calculated timeout to behave unpredictably at high `max_tokens` values.
**Blocks sessions:** S3 (re-seed cannot complete without this fix)

## Pre-Flight Checks
Before making any changes:
1. Run the test suite:
   ```
   python -m pytest -n auto -q
   ```
   Expected: 161 passed, 3 skipped, 3 pre-existing errors
2. Verify git is clean: `git status`
3. Read the affected file to understand current state:
   - `app/segmentation.py`

## Objective
Increase `max_tokens` in `segment_transcript()` so Claude's JSON response is not truncated for transcripts up to ~150K characters. Add an explicit timeout to the Anthropic client so large requests fail predictably rather than hanging.

This is a targeted fix, not a feature session. Keep changes minimal and focused.

## Requirements

1. **In `segment_transcript()`:** Change `max_tokens=4096` to `max_tokens=32000`.

   Rationale: The largest transcript is ~136K chars ≈ 34K tokens of input. The output is approximately the same size (verbatim text in JSON) plus ~10% overhead for JSON structure, labels, and speaker arrays. 32000 output tokens provides headroom for transcripts up to ~120K tokens of output. This covers our current transcripts with margin.

   Do NOT change `max_tokens` in `generate_event_label()` — that function returns a 3-5 word label and 4096 is more than sufficient.

2. **In `_create_client()`:** Add `timeout=120.0` to the `anthropic.Anthropic()` constructor.

   Rationale: 120 seconds is 2× the sprint spec benchmark of <60s per transcript. If a call exceeds this, it's genuinely stuck, not just slow. The explicit timeout also overrides the SDK's auto-calculated timeout, which rejects high `max_tokens` values on non-streaming calls.

3. **Add one regression test in `tests/test_segmentation.py`:**
   - `test_segment_transcript_max_tokens` — mock the Claude client, call `segment_transcript()` with a valid response, and assert that the `max_tokens` kwarg passed to `client.messages.create()` is `32000` (not 4096).

## Constraints
- Do NOT modify any files except `app/segmentation.py` and `tests/test_segmentation.py`
- Do NOT modify: any other `app/` files, any `scripts/` files, `static/index.html`, any other test files
- Do NOT refactor or improve code beyond the specific fix
- Do NOT add features, optimizations, or enhancements
- Do NOT change `generate_event_label()` in any way
- Keep the change surface as small as possible

## Affected Files
| File | Change |
|------|--------|
| `app/segmentation.py` | `max_tokens` 4096→32000 in `segment_transcript()`; `timeout=120.0` in `_create_client()` |
| `tests/test_segmentation.py` | Add 1 regression test for max_tokens value |

## Test Targets
After implementation:
- Existing tests: all must still pass (including existing 8 tests in test_segmentation.py)
- New test: `test_segment_transcript_max_tokens`
- Minimum new test count: 1
- Test command: `python -m pytest tests/test_segmentation.py -x -q` (scoped) then `python -m pytest -n auto -q` (full)

## Definition of Done
- [ ] `max_tokens=32000` in `segment_transcript()` API call
- [ ] `timeout=120.0` in `_create_client()` Anthropic constructor
- [ ] `generate_event_label()` unchanged
- [ ] 1 new regression test written and passing
- [ ] All existing tests pass
- [ ] No unrelated changes made
- [ ] Change is minimal and focused (should be a 3-line diff plus test)

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| Fix addresses the stated issue | `grep max_tokens app/segmentation.py` shows 32000 in segment_transcript |
| Timeout is set | `grep timeout app/segmentation.py` shows 120.0 |
| generate_event_label unchanged | `grep -A5 generate_event_label app/segmentation.py` still shows max_tokens=4096 |
| No unrelated files modified | `git diff --name-only` shows only `app/segmentation.py` and `tests/test_segmentation.py` |
| All tests pass | Full suite passes |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include the structured JSON appendix.

**Write the close-out report to a file:**
docs/sprints/sprint-3.5/session-s3f1-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3.5/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3.5/session-f1-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (scoped): `python -m pytest tests/test_segmentation.py -x -q`
5. Files that should NOT have been modified: everything except `app/segmentation.py` and `tests/test_segmentation.py`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3.5/session-s3f1-review.md

## Session-Specific Review Focus (for @reviewer)
1. Verify only `max_tokens` in `segment_transcript()` changed (not in `generate_event_label()`)
2. Verify `timeout=120.0` is on the client constructor, not on individual API calls
3. Verify the new test actually asserts the `max_tokens` value
4. Verify no other behavioral changes to either public function
5. Verify change surface is minimal (should be ~3 lines changed plus test)

## Sprint-Level Regression Checklist
- Pre-sprint: 147 passed, 3 skipped, 3 pre-existing errors
- Hard floor: ≥118 pass
- All critical invariants from review-context.md must hold

## Sprint-Level Escalation Criteria
1. Test pass count drops below 118
2. Any file outside the two affected files modified