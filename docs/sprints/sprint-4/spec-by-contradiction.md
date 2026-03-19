# Sprint 4: What This Sprint Does NOT Do

## Out of Scope
1. **Cross-transcript label uniqueness enforcement:** Labels are deduped within a single transcript/batch only. Enforcing uniqueness across all historical labels adds token cost and coupling for marginal value at current data volume. Deferred.
2. **Archetype glyphs for dynamic clusters:** New clusters created below threshold get no glyph_id (NULL). Glyph design requires Jessie's input and is a visual concern for Sprint 5.
3. **Rolling centroid updates:** When new events join a cluster, the centroid is not recomputed. The initial centroid (event embedding for dynamic clusters, representative text embedding for seed clusters) remains fixed. Centroid evolution is a Phase 2+ concern.
4. **Frontend changes:** No modifications to `static/index.html`. The frontend already handles clusters with null glyph_id and varying event counts. API contract is unchanged.
5. **Transcript dedup (DEF-018):** Preventing re-upload of the same transcript is a separate concern. This sprint stores transcripts but does not check for duplicates.
6. **Label regeneration endpoint/UI:** Labels can be regenerated via a backfill script. No API endpoint or UI for on-demand regeneration.
7. **Dynamic XS_CENTERS for new clusters:** New clusters use the existing `_DEFAULT_XS_CENTER = 0.50`. Assigning meaningful semantic-spectrum positions to emergent clusters requires design thought beyond this sprint's scope.
8. **Significance score storage on events:** The significance score is used for filtering only. It is not stored on the event row. If needed later, it can be added as a column.
9. **Archetype renaming when cluster composition shifts:** Once a cluster is named (at event_count ≥ 3), the name is permanent for this sprint. Renaming based on evolving cluster content is a future enhancement.

## Edge Cases to Reject
1. **Significance score missing from Claude response:** If the segmentation API returns a segment without a significance field, treat as significance = 1.0 (include by default). Log a warning. Do not fail the pipeline.
2. **All segments below threshold in a transcript:** Store the transcript in raw_inputs, return empty event list. Do not raise an error — this is a valid outcome.
3. **Archetype naming API failure:** If Claude fails to generate a name when event_count reaches threshold, keep "The Unnamed" and log an error. Retry on next event insertion to the cluster. Do not block the pipeline.
4. **Telegram message from unknown user that is below threshold:** Store in raw_inputs with participant="unknown". Do not create an event. This is the correct behavior.
5. **Empty Telegram message after significance check:** Already handled by existing empty-text check before significance scoring.
6. **New cluster created but no subsequent events join it:** A cluster of one is valid. It stays as "The Unnamed" indefinitely (below naming threshold). This is acceptable for v1.
7. **Two below-threshold events in the same batch that are similar to each other:** The second event should join the first event's new cluster (centroids are refreshed mid-batch). Do not create two separate clusters.

## Scope Boundaries
- **Do NOT modify:** `app/main.py` (no route changes), `app/myth.py`, `app/embedding.py`, `static/index.html`
- **Do NOT optimize:** Embedding calls (one per segment is fine), centroid lookup (linear scan is fine at current scale)
- **Do NOT refactor:** The pipeline duplication between `app/granola.py` and `scripts/seed_transcript.py` — they share a pattern but serve different contexts (live upload vs. batch seeding). Consolidation is deferred.
- **Do NOT add:** New API endpoints, new frontend features, new input sources, rate limiting on significance scoring

## Interaction Boundaries
- This sprint does NOT change the behavior of: `/events` GET, `/clusters` GET, `/myth` POST endpoints. Response schemas are unchanged. New nullable columns on events are excluded from the existing select list unless explicitly needed.
- This sprint does NOT affect: Frontend rendering, myth generation logic, embedding model or dimensions, existing seed cluster centroids or their is_seed status.

## Deferred to Future Sprints

| Item | Target Sprint | DEF Reference |
|------|--------------|---------------|
| Transcript dedup | Sprint 5+ | DEF-018 |
| Archetype glyphs for dynamic clusters | Sprint 5 | — |
| Rolling centroid recomputation | Phase 2+ | — |
| Dynamic XS_CENTERS for new clusters | Sprint 5+ | — |
| Label regeneration endpoint | Unscheduled | — |
| Cross-transcript label uniqueness | Unscheduled | — |
| Archetype renaming on composition shift | Unscheduled | — |
| Significance score storage on event rows | Unscheduled | — |
