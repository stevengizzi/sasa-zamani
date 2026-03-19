# Sprint 2: Escalation Criteria

## Session-Level Escalation (→ Work Journal)

1. **Compaction recovery:** Any session requires more than 1 context recovery attempt → log in work journal, assess whether session scope needs splitting.
2. **Test failure cascade:** A session's changes cause 5+ existing tests to fail → stop, log in work journal, assess root cause before continuing.
3. **Frontend rendering regression:** A change that should only affect data loading breaks the animated transition, panel system, or view toggle → log in work journal, revert and reassess.
4. **xs computation produces degenerate layout:** Events from 3+ different clusters overlap within a 20px visual radius in strata view → log in work journal, reassess computation approach.

## Sprint-Level Escalation (→ Tier 3 Review)

5. **Double compaction failure:** Any session exceeds 2 compaction recovery attempts → halt sprint, Tier 3 review of session scope and file architecture.
6. **DEC-005 pressure:** Frontend single-file architecture produces merge conflicts between sessions or makes changes unmanageable (multiple session implementers cannot reason about the file) → escalate to Tier 3 for possible DEC-005 reconsideration.
7. **Myth quality failure (RSK-002):** More than 30% of generated myths (tested across all 6 seed clusters) produce therapy-speak, generic wisdom, or prohibited words from the design reference → halt myth integration, escalate for prompt engineering sprint.
8. **API shape incompatibility:** Frontend data layer requires API response fields that cannot be added without breaking existing consumers → escalate for API versioning decision.
9. **Canvas performance collapse:** Frame rate drops below 15fps with <100 events in either view → escalate for rendering architecture review.

## Decision Escalation (→ New DEC entry)

10. **xs computation approach change:** If cluster-center + offset produces visually unusable layouts during S2 visual review → new DEC needed for alternative approach.
11. **Edge rendering removal:** If cluster co-membership edges look worse than no edges → new DEC to decide: ship without edges or invest in embedding similarity this sprint.
12. **Myth caching strategy change:** If the 3-event-delta regeneration trigger fires too often or not often enough during testing → new DEC for trigger threshold.
