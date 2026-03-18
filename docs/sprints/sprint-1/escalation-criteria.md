# Sprint 1: Escalation Criteria

These conditions should trigger an immediate stop and human review. Do not attempt to work around them in the implementation session.

## Infrastructure Escalations

1. **Supabase pgvector unavailable:** If the pgvector extension cannot be enabled or the `vector` column type is not recognized, STOP. The entire embedding storage strategy depends on this. Do not fall back to storing embeddings as JSON arrays.

2. **Railway deployment fails 3+ consecutive times:** If deployment repeatedly fails after fixing the obvious causes (missing env vars, wrong Python version, dependency conflicts), STOP. Do not switch hosting providers within the sprint.

3. **OpenAI embedding dimension mismatch:** If `text-embedding-3-small` returns vectors with dimensions ≠ 1536, STOP. The database schema is hardcoded to `vector(1536)`. A dimension change means the model has been updated or the wrong model is being called.

## Data Quality Escalations

4. **Degenerate cluster assignment:** If, during testing with varied input text, all or nearly all events (>80%) are assigned to the same cluster, STOP. This means either the seed centroids are too similar to each other, or the embedding space doesn't differentiate the archetype domains. This is RSK-001 materializing. Log the similarity scores and escalate for centroid redesign.

5. **Cosine similarity scores uniformly high or low:** If similarity between events and their best-matching centroid is consistently > 0.95 or < 0.1 across diverse inputs, the similarity metric may not be meaningful at this embedding scale. STOP and investigate before proceeding with pipeline wiring.

## Scope Escalations

6. **Any session exceeds 2× estimated test count:** If a session requires more than double the estimated tests to achieve coverage, this signals the session scope was underestimated. Finish the current tests, close out, and escalate for session re-scoping.

7. **Supabase client library incompatibility:** If `supabase-py` does not support pgvector operations (insert, query with `<=>` operator) natively and requires raw SQL for all vector operations, document the workaround in the close-out but escalate if it adds more than ~20 lines of raw SQL. The architectural assumption was that the client library handles this.

8. **Telegram webhook registration requires a different architecture:** If Telegram's webhook setup requires a different endpoint structure than POST /telegram (e.g., needs path-based routing or specific response formats not compatible with FastAPI's default behavior), document and escalate rather than restructuring the API.

## Process Escalations

9. **Compaction in Session 4b:** If context compaction occurs during Session 4b (the Critical-scored session), STOP the session, write a partial close-out, and create a follow-up session for remaining work. Do not attempt to recover in the same session.
