# Sprint 3 — Session S3 Review: Myth Prompt Refinement

**Reviewer:** @reviewer (Tier 2)
**Date:** 2026-03-19
**Commit:** 948837a `feat(sprint-3): S3 myth prompt refinement (FF-005)`

---

## Verdict: PASS

## Summary

Clean, focused prompt refinement. Only `build_myth_prompt` was modified in `app/myth.py`; caching and generation functions are untouched. All 15 myth tests pass. No forbidden files were modified. The prompt reads like marginalia, not wellness.

---

## Checklist Results

| # | Focus Item | Result | Notes |
|---|-----------|--------|-------|
| 1 | `build_myth_prompt` includes "ancestral", "marginalia", "scholar" | PASS | All three terms present in the prompt string |
| 2 | Thin-cluster path triggers at <=2 events, shorter word target, "still forming" | PASS | `is_thin = event_count <= 2` gates 10-20 word target and "The constellation is still forming" framing |
| 3 | PROHIBITED_WORDS and PREFERRED_WORDS enforced in prompt | PASS | Both constants unchanged; both injected at end of prompt via `Do NOT use these words:` and `Prefer these words:` |
| 4 | `should_regenerate`, `generate_myth`, `get_or_generate_myth` NOT modified | PASS | Diff confirms only `build_myth_prompt` was touched in `app/myth.py` (lines 27-61). Functions at lines 64-114 are identical to prior commit |
| 5 | Myth caching logic (version, delta) untouched | PASS | `should_regenerate` delta>=3 logic, `get_or_generate_myth` version increment, `insert_myth`/`update_cluster_myth` calls — all unchanged |
| 6 | Sample prompt tonal assessment | PASS | See below |

## Forbidden File Check

No forbidden files modified. The S3 commit touches: `app/myth.py`, `tests/test_myth.py`, `scripts/test_myth_quality.py` (new), `pyproject.toml`, `docs/` files only.

## Test Verification

```
python -m pytest tests/test_myth.py -x -q
15 passed in 0.23s
```

All 15 myth tests pass, including the 3 new tests (`test_includes_register_guidance`, `test_thin_cluster`, `test_normal_cluster`).

## Sample Prompt Trace

Tracing `build_myth_prompt("The Gate", ["dreamed about crossing a threshold", "the door that appeared in the fog"])`:

- `event_count = 2`, `is_thin = True`
- `length_target = "Write one sentence (10-20 words)."`
- `thin_framing` includes "still forming" text

Output:

> You are speaking in an ancestral register. Ancestral and exact. A scholar who has spent years inside a subject, now speaking plainly about it to someone they respect.
>
> Not wellness. Not witchy. Not fantasy. Not therapy-speak. Not generic wisdom.
>
> If it sounds like a wellness app, discard it. If it sounds like a technical manual, discard it. If it sounds like marginalia in an old book, keep it.
>
> This sentence could not have been written without these specific events. If it could apply to anyone's life, discard it and try again.
>
> Archetype: The Gate
> This constellation holds 2 moments.
> Events in this cluster:
> - dreamed about crossing a threshold
> - the door that appeared in the fog
>
> Write one sentence (10-20 words). Name what this cluster is actually about — what thread runs through all these moments. Speak as if from the past looking forward. No quotation marks.
> The constellation is still forming. Name the thread that is beginning to appear.
>
> Do NOT use these words: detect, discover, reveal, collective unconscious, synchronicity, universe, field, activate, activation, signal, journey, transformation, powerful, growth, explore, reflect, unlock
>
> Prefer these words where they fit naturally: scaffold, propose, candidate, resonate, vessel, compost, harvest window, rhyme, constellation, intersubjective, meaning-making, narrative commons

**Tonal assessment:** The prompt firmly steers toward the ancestral register. The layered rejection criteria ("not wellness, not witchy, not fantasy, not therapy-speak") combined with the positive framing ("scholar... speaking plainly") and the marginalia test create a strong tonal funnel. The embarrassment test ("could not have been written without these specific events") is well placed. This reads like instructions to a scribe, not a life coach.

## Findings

No CONCERN or FAIL findings.

### Observations (informational only)

1. **OBS-01: Updated existing test assertion.** `test_includes_ancestral_register_instruction` changed from asserting `"not explanation, not analysis"` to `"Ancestral and exact"`. This is appropriate — the old wording no longer exists in the prompt. The test still validates the ancestral register instruction.

2. **OBS-02: `pyproject.toml` addition.** Adding `testpaths = ["tests"]` is a reasonable scope addition to prevent pytest from collecting `scripts/test_myth_quality.py`. This is a standard pytest configuration and has no side effects.

3. **OBS-03: `scripts/test_myth_quality.py` uses bare `generate_myth` (live API call).** The script calls `generate_myth` directly, which makes a real Anthropic API call and costs money per invocation. This is by design for manual quality testing, but worth noting — it should never be added to CI.

## Recommendation

No post-review fixes needed.
