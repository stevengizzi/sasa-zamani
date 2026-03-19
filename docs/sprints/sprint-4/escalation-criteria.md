# Sprint 4: Escalation Criteria

## Tier 3 Architectural Escalation

Trigger a Tier 3 review if any of the following occur:

1. **Significance score distribution is degenerate.** If re-seeded data produces significance scores that are >90% above threshold OR >90% below threshold, the prompt is not discriminating. Pause and redesign the significance prompt before continuing.

2. **Cluster explosion.** If re-seeding the existing 48 events (pre-filter) produces more than 15 new clusters, the cluster_join_threshold is too high relative to the embedding space. Pause and evaluate threshold tuning before proceeding.

3. **DEF-021 reveals a platform limit.** If the 10,243-char truncation is caused by a Supabase row size limit, Railway request body limit, or other infrastructure constraint that cannot be fixed with a code change, escalate for an architectural decision (e.g., chunked storage, external blob store).

4. **Archetype naming produces consistently poor names.** If ≥50% of generated archetype names fail the Copy Tone test (wellness-speak, therapy-speak, vague abstractions like "The Journey"), escalate for prompt redesign with design-reference.md as primary reference.

5. **Raw input storage changes the API contract.** If the raw_inputs FK or new event columns unexpectedly appear in `/events` GET responses, the frontend may break. This should not happen (the select list is explicit), but if it does, escalate immediately.

## Session-Level Escalation

6. **Segmentation prompt returns malformed significance.** If Claude returns significance values outside 0.0–1.0, or returns non-numeric significance, and the fallback-to-1.0 path fires for >30% of segments, the prompt needs redesign before proceeding to pipeline integration.

7. **Migration script fails on production.** If `migrate_sprint4.sql` fails against the live Supabase instance (column conflicts, FK violations), do not attempt manual fixes. Escalate with the exact error.

8. **Centroid refresh causes performance regression.** If refreshing centroids after each new cluster creation makes a single transcript upload take >120s, consider batching centroid refreshes (refresh once at end of batch, accept that mid-batch events may create redundant clusters).
