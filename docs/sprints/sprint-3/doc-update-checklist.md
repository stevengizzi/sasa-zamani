# Sprint 3: Doc Update Checklist

After Sprint 3 completes, the following documents need updates:

## Required Updates

- [ ] **`docs/project-knowledge.md`**
  - Update "Current State" section: test count, sprints completed, active sprint
  - Add Sprint 3 to sprint list
  - Update "Key Active Decisions" if any new DECs created (DEC-015–017 reserved)
  - Note Gate/Silence xs adjustment (pending Jessie review)

- [ ] **`docs/sprint-history.md`**
  - Add Sprint 3 entry: goal, sessions, test delta, key outcomes, carry-forwards, review verdicts

- [ ] **`docs/architecture.md`**
  - Update "Components" section if seed_transcript.py adds a notable new pipeline path
  - Note atomic increment_event_count change
  - Note glyph_id population in seed_clusters

- [ ] **`docs/decision-log.md`**
  - Add any new DEC entries (DEC-015–017 reserved)
  - Update DEC-011 (seed clusters) if xs center change warrants logging

- [ ] **`docs/dec-index.md`**
  - Add index entries for any new DECs

- [ ] **`docs/risk-register.md`**
  - Update RSK-002 (myth fable risk) severity based on prompt refinement results
  - Update RSK-003 (habit loop) if FF-004 seeding addresses the "empty map" aspect
  - Update RSK-004 (frontend scope creep) if S4 scope stayed bounded

- [ ] **`docs/roadmap.md`**
  - Mark Sprint 3 as complete
  - Update deferred items table:
    - Close: DEF-010, DEF-011, DEF-012, DEF-013, DEF-014, DEF-016
    - Add: DEF-017 (myth post-validation), DEF-018 (transcript dedup)
  - Update Sprint 4 scope if Sprint 3 outcomes affect it
  - Note FF-004 as implemented

- [ ] **`CLAUDE.md`**
  - Update test count baseline
  - Note new scripts: `seed_transcript.py`, `test_myth_quality.py`
  - Note resolved deferred items

## Conditional Updates

- [ ] **`docs/decision-log.md` — Gate/Silence xs centers**
  Only if Jessie confirms or revises the 0.08/0.20 values. If she changes them, log as a new DEC.

- [ ] **`docs/risk-register.md` — RSK-002 severity change**
  Only if myth prompt results warrant changing severity from Medium. Could go to Low (prompt works well) or stay Medium (still needs work).
