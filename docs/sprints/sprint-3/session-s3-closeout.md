---BEGIN-CLOSE-OUT---

**Session:** Sprint 3 — S3 Myth Prompt Refinement
**Date:** 2026-03-19
**Self-Assessment:** MINOR_DEVIATIONS

### Change Manifest
| File | Change Type | Rationale |
|------|-------------|-----------|
| app/myth.py | modified | Refined `build_myth_prompt` with expanded register, embarrassment test, event count, thin-cluster handling |
| tests/test_myth.py | modified | Added 3 new tests; updated existing register assertion to match new wording |
| scripts/test_myth_quality.py | added | Manual myth quality testing script for live cluster data |
| pyproject.toml | modified | Added `testpaths = ["tests"]` to prevent pytest collecting scripts/ |

### Judgment Calls
- Updated the existing `test_includes_ancestral_register_instruction` assertion from `"not explanation, not analysis"` to `"Ancestral and exact"` since the prompt wording changed. The test still validates the ancestral register instruction is present.
- Added `testpaths = ["tests"]` to pyproject.toml to prevent pytest from collecting `scripts/test_myth_quality.py` as a test file. Without this, the full suite would show a collection error for the script (which requires live API keys).

### Scope Verification
| Spec Requirement | Status | Implementation |
|-----------------|--------|----------------|
| Expanded register instructions | DONE | app/myth.py:build_myth_prompt — "Ancestral and exact", scholar framing, anti-wellness, marginalia test |
| Embarrassment test instruction | DONE | app/myth.py:build_myth_prompt — "could not have been written without these specific events" |
| Event count context | DONE | app/myth.py:build_myth_prompt — "This constellation holds {N} moments" |
| Thin-cluster handling (≤2 events) | DONE | app/myth.py:build_myth_prompt — 10-20 words target, "still forming" framing |
| PROHIBITED_WORDS preserved | DONE | Constant and enforcement pattern unchanged |
| PREFERRED_WORDS preserved | DONE | Constant and enforcement pattern unchanged |
| scripts/test_myth_quality.py | DONE | Manual script, connects to Supabase, fetches clusters, generates myths, prints summary |
| 3 new tests | DONE | test_includes_register_guidance, test_thin_cluster, test_normal_cluster |
| All existing tests pass | DONE | 147 passed, 3 skipped, 3 pre-existing errors |

### Regression Checks
| Check | Result | Notes |
|-------|--------|-------|
| `should_regenerate` logic unchanged | PASS | Function not modified; existing tests pass |
| `generate_myth` fallback on error unchanged | PASS | Function not modified; existing tests pass |
| `get_or_generate_myth` caching logic unchanged | PASS | Function not modified; existing tests pass |
| PROHIBITED_WORDS constant still present | PASS | `grep` confirms 2 occurrences in app/myth.py |
| Function signature unchanged | PASS | `build_myth_prompt(cluster_name: str, event_labels: list[str]) -> str` |

### Test Results
- Tests run: 150
- Tests passed: 147
- Tests failed: 0
- Tests skipped: 3
- Errors: 3 (pre-existing FK constraint teardown in integration tests)
- New tests added: 3
- Command used: `python -m pytest -n auto -q`

### Unfinished Work
None

### Notes for Reviewer
- The 3 errors in the test suite are pre-existing FK constraint teardown issues in `test_clustering.py::TestSeedClustersIntegration` — documented in sprint context as expected.
- The existing test `test_includes_ancestral_register_instruction` was updated to assert `"Ancestral and exact"` instead of `"not explanation, not analysis"` since the prompt wording changed. This is a necessary update, not a regression.

---END-CLOSE-OUT---

```json:structured-closeout
{
  "schema_version": "1.0",
  "sprint": "3",
  "session": "S3",
  "verdict": "COMPLETE",
  "tests": {
    "before": 144,
    "after": 147,
    "new": 3,
    "all_pass": true
  },
  "files_created": ["scripts/test_myth_quality.py"],
  "files_modified": ["app/myth.py", "tests/test_myth.py", "pyproject.toml"],
  "files_should_not_have_modified": [],
  "scope_additions": [
    {
      "description": "Added testpaths to pyproject.toml",
      "justification": "Prevent pytest from collecting scripts/test_myth_quality.py as a test, which would fail due to missing live API keys"
    }
  ],
  "scope_gaps": [],
  "prior_session_bugs": [],
  "deferred_observations": [],
  "doc_impacts": [],
  "dec_entries_needed": [],
  "warnings": [],
  "implementation_notes": "Prompt refinement was straightforward. The thin-cluster threshold of ≤2 events triggers a shorter word target and 'still forming' framing. The expanded register draws directly from the Design Brief Copy Tone section. Updated one existing test assertion to match new prompt wording."
}
```
