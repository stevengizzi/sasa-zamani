# Sprint 3, Session S2 — Tier 2 Review Report

**Date:** 2026-03-19
**Reviewer:** @reviewer subagent
**Session:** S2 — Granola Transcript Seeding (FF-004)
**Verdict:** CONCERNS

## Review Checklist

### 1. No Existing app/ Files Modified
**PASS**: `git diff HEAD~1 --name-only` confirms only four new files were added: `scripts/seed_transcript.py`, `tests/test_seed_transcript.py`, `docs/sprints/sprint-3/session-s2-closeout.md`, and `dev-logs/2026-03-19-sprint3-s2.md`. No existing `app/` files, `static/index.html`, or existing test files were modified.

### 2. Speaker Remapping
**PASS**: `parse_transcript()` accepts a `speaker_map` dict and `default_participant` string. Mapped speakers (e.g., `"Speaker A"` -> `"steven"`) are resolved via `speaker_map.get(speaker_label, default_participant)`. Unmapped speakers fall through to `default_participant` (default `"shared"`). This correctly handles both March 17 (3 speakers, all mapped) and March 18 (9 speakers, 3 mapped, 6 defaulting to shared). The regex `^(Speaker [A-Z]):\s*` correctly captures single-letter speaker labels.

### 3. Dry-Run Isolation
**PASS**: When `--dry-run` is set, `main()` calls `print_dry_run()` and returns immediately (line 224-226). `run_pipeline()` is never called. The test `test_dry_run_no_api_calls` patches both `embed_text` and `insert_event` and verifies neither is called. No API or DB imports are invoked during dry-run since `print_dry_run` only reads from the already-parsed segment list.

### 4. Error Handling (Skip, Don't Abort)
**PASS with caveat**: Embedding errors (`EmbeddingError`) on lines 153-158 correctly skip the segment and continue. DB insert errors on lines 160-174 correctly skip the segment and continue. `increment_event_count` failures on lines 176-181 are logged as warnings without skipping. The xs computation block on lines 183-190 catches exceptions. See Concern #1 for an edge case in the xs error path.

### 5. Pipeline Matches process_granola_upload
**PASS with caveat**: The pipeline steps in `run_pipeline()` match `process_granola_upload()` in order and substance:

| Step | `process_granola_upload` | `run_pipeline` | Match |
|------|--------------------------|----------------|-------|
| Centroids | `get_cluster_centroids()` before loop | `get_cluster_centroids()` before loop | Yes |
| Embed | `embed_text(segment["text"])` | `embed_text(text)` | Yes |
| Assign | `assign_cluster(embedding, centroids)` | `assign_cluster(embedding, centroids)` | Yes |
| Label | `segment["text"][:80]` (conditional) | `text[:80]` (unconditional slice) | Equivalent |
| Insert | `insert_event(label, note, participant, embedding, "granola", cluster_id)` | Same args | Yes |
| Increment | `increment_event_count(cluster_id)` with try/except warning | Same | Yes |
| XS | `get_cluster_by_id` -> `compute_xs` -> `update_event_xs` | Same | Yes |

The intentional difference is error handling strategy: `process_granola_upload` fails fast on embedding errors (no partial writes), while `run_pipeline` skips individual failures (appropriate for batch seeding). See Concern #1 for a subtle difference in where `get_cluster_by_id` sits relative to the try/except.

### 6. Min-Length Filter Uses Character Count
**PASS**: `filter_by_length()` on line 118 uses `len(s["text"])` which returns the character count of the string, not word count. The `--min-length` argument help text explicitly says "Minimum segment character length" (line 69). Default is 100. The test `test_min_length_filter_excludes_short` verifies short strings are excluded, and `test_min_length_filter_includes_long` verifies `"x" * 150` passes the 100-char threshold.

## Test Verification
```
7 passed, 1 warning in 0.55s
```
All 7 tests pass: `test_speaker_remapping_known`, `test_speaker_remapping_unknown_defaults_shared`, `test_min_length_filter_excludes_short`, `test_min_length_filter_includes_long`, `test_dry_run_no_api_calls`, `test_end_to_end_mock_pipeline`, `test_embedding_error_skips_segment`.

## Scope Compliance
- **Files created:** `scripts/seed_transcript.py`, `tests/test_seed_transcript.py`, `docs/sprints/sprint-3/session-s2-closeout.md`, `dev-logs/2026-03-19-sprint3-s2.md` -- all expected.
- **Files modified:** None -- correct.
- **Protected files untouched:** All `app/` files, `static/index.html`, existing test files -- confirmed untouched.

## Concerns

1. **LOW — UnboundLocalError if `get_cluster_by_id` raises inside the xs try block.** In `run_pipeline()` lines 183-194, `cluster` is assigned inside a try/except block (line 184). If `get_cluster_by_id(cluster_id)` raises an exception, the `except` on line 189 logs a warning but does not set `cluster`. Control then falls through to line 192 which references `cluster` -- this would raise `UnboundLocalError`, which is uncaught and would crash the script. In contrast, `process_granola_upload` places `get_cluster_by_id` outside the try/except (line 120), so this pattern does not apply there. Fix: either initialize `cluster = None` before the try block, or move `get_cluster_by_id` outside the try/except to match `process_granola_upload`.

## Overall Assessment

Clean session with two new files, no modifications to existing code, and solid test coverage (7 tests). The pipeline faithfully mirrors `process_granola_upload` with the intentional addition of per-segment error resilience. Speaker remapping, dry-run isolation, character-count filtering, and error-skip behavior all work correctly and are tested. One LOW-severity concern: a potential `UnboundLocalError` if `get_cluster_by_id` throws, which would crash the batch run instead of skipping the segment. This is an unlikely edge case (requires a Supabase error mid-run on a read call) but contradicts the "skip, don't abort" design intent. Recommend a one-line fix (`cluster = None` before the try block) before the live seeding run.
