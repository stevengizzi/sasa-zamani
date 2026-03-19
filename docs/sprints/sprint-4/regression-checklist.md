# Sprint 4: Regression Checklist

## Pre-existing Invariants (must pass at every session close-out)

- [ ] All 166 pre-Sprint 4 tests pass
- [ ] `/events` GET returns valid JSON array with existing field schema (id, created_at, event_date, label, note, participant, source, cluster_id, xs, day, participants)
- [ ] `/events` GET response does NOT include raw_input_id, start_line, or end_line (API contract unchanged)
- [ ] `/clusters` GET returns valid JSON array with existing field schema
- [ ] `/myth` POST still generates myths for existing seed clusters
- [ ] Telegram webhook processes a text message end-to-end (extract → embed → assign → store)
- [ ] Granola upload processes a transcript end-to-end (segment → embed → assign → store)
- [ ] `event_date`, `participants`, `xs` fields populated correctly on new events
- [ ] Existing seed cluster centroids not modified (is_seed=True clusters unchanged)
- [ ] `compute_xs()` works for both seed clusters (via XS_CENTERS) and new clusters (via _DEFAULT_XS_CENTER)
- [ ] `increment_event_count()` RPC still works for both seed and dynamic clusters

## Sprint 4 Specific Invariants

- [ ] New config fields (`significance_threshold`, `archetype_naming_threshold`) have defaults — app starts without them set in env
- [ ] `insert_event()` is backward-compatible — existing callers that don't pass raw_input_id/start_line/end_line still work
- [ ] `segment_transcript()` still returns valid Segment objects — new fields (start_line, end_line, significance) are populated
- [ ] `generate_event_label()` new return type (tuple) is handled by all callers
- [ ] `assign_cluster()` still exists and works unchanged (backward compatibility for any callers not yet migrated)
- [ ] `assign_or_create_cluster()` returns correct 3-tuple (cluster_id, similarity, created)
- [ ] Dynamic clusters inserted with is_seed=False, name="The Unnamed", valid centroid
- [ ] `maybe_name_cluster()` is safe to call on seed clusters (no-op, not "The Unnamed")
- [ ] `maybe_name_cluster()` is safe to call on clusters below naming threshold (no-op)
- [ ] `raw_inputs` table accessible via Supabase client
- [ ] `ensure_schema()` now validates raw_inputs table exists
- [ ] Dedup labels function does not mutate input list
- [ ] Significance filter does not mutate input list
