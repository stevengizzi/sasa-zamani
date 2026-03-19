# Sprint 3: Escalation Criteria

## Tier 3 Review Triggers

Escalate to a Tier 3 architectural review conversation if any of the following occur:

1. **Atomic increment implementation requires schema change.** If making `increment_event_count` atomic via single SQL UPDATE is blocked by the Supabase client library and requires a Postgres function (RPC), a stored procedure, or a schema migration — that's infrastructure work beyond the sprint scope. Escalate before implementing.

2. **Seeding script produces >500 events.** The estimate is ~393. If the actual count significantly exceeds this (e.g., due to segment splitting behavior), pause and assess whether the frontend can handle the load and whether the demo experience is degraded by too many nodes.

3. **Myth output consistently fails tonal test.** If after 3+ prompt iterations, myth output for real cluster data still reads as wellness-speak, therapy language, or generic wisdom — the prompt engineering approach may be insufficient. Escalate to discuss whether the prompt architecture (single-shot generation) needs to change.

4. **Frontend changes break existing interactions.** If adding Esc key, reverse chaining, or fade animation causes regressions in panel open/close, chained navigation, view transition, or participant toggle — stop and escalate rather than patching. The 48K single-file frontend is fragile; cascading fixes signal structural risk.

5. **Existing test count drops below 118 pass.** The baseline is ~122 pass, 3 skip. A drop of more than 4 passing tests indicates a regression that needs investigation before continuing.

## In-Session Escalation (for implementer)

During any session, escalate to the Work Journal if:

- A file not listed in the session's "Modifies" column needs changes
- A new file not listed in the session's "Creates" column is needed
- The session's test count will exceed the estimate by more than 50%
- An external service (OpenAI, Anthropic, Supabase) behaves unexpectedly
- A deferred item fix reveals a deeper architectural issue than expected

## Decision Escalation

Reserve DEC-015 through DEC-017. Create a new DEC entry if:

- The atomic increment approach requires choosing between alternative implementations
- The transcript seeding approach needs to change (e.g., segment merging instead of filtering)
- The myth prompt architecture changes (e.g., multi-shot, chain-of-thought, or different model)
- Any Sprint 3 work contradicts an existing DEC entry
