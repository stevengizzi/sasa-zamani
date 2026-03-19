# Sprint 3: Regression Checklist

## Test Suite Baseline

- **Pre-sprint:** ~125 collected, ~122 pass, ~3 skip
- **Post-sprint target:** ~146 collected, ~143 pass, ≤3 skip
- **Hard floor:** ≥118 pass (drop of >4 from baseline = escalation trigger)

Run full suite at session close: `pytest -n auto`

## Critical Invariants

### API Endpoint Contracts (must not change)

- [ ] `GET /events` returns list of `EventResponse` objects with fields: `id`, `created_at`, `event_date`, `label`, `note`, `participant`, `source`, `cluster_id`, `xs`, `day`
- [ ] `GET /events?participant=jessie` filters correctly (case-insensitive)
- [ ] `GET /clusters` returns list of `ClusterResponse` objects with fields: `id`, `name`, `glyph_id`, `myth_text`, `myth_version`, `event_count`, `last_updated`, `is_seed`
- [ ] `POST /telegram` always returns 200 (even on error — prevents Telegram retry storms)
- [ ] `POST /granola` returns `{"events": [...]}` on success, 400 on bad input, 503 on pipeline failure
- [ ] `POST /myth` returns `MythResponse` with `myth_text` and `cached` fields
- [ ] `GET /health` returns `HealthResponse` with `status` and `database` fields

### Telegram Pipeline (happy path)

- [ ] `extract_message` correctly parses update dict → (text, participant, update_id)
- [ ] `is_duplicate` returns False for new update_ids, True for seen ones
- [ ] `process_telegram_update` returns `{"processed": True, "reason": "ok", "event_id": "..."}` for valid messages
- [ ] Participant mapping resolves by username, full name, or first name (in that order)
- [ ] Event is stored with correct label, note, participant, source="telegram", cluster_id, xs

### Granola Pipeline (happy path)

- [ ] `parse_transcript` splits on speaker labels, attributes participants
- [ ] `process_granola_upload` embeds, assigns cluster, stores event, increments count, computes xs
- [ ] Empty transcript → ValueError
- [ ] Embedding failure → EmbeddingError raised (no partial writes)

### Myth Generation

- [ ] `build_myth_prompt` produces a non-empty string containing cluster name and event labels
- [ ] `should_regenerate` returns True when no cached myth exists
- [ ] `should_regenerate` returns True when event count delta ≥ 3
- [ ] `should_regenerate` returns False when event count delta < 3
- [ ] `generate_myth` returns fallback "The pattern holds." on API error
- [ ] `get_or_generate_myth` returns cached myth when fresh
- [ ] `get_or_generate_myth` calls Claude and caches when stale
- [ ] Myth caching logic (version increment, insert_myth, update_cluster_myth) is unchanged

### Frontend (visual verification — S4 review and S5 walkthrough)

- [ ] Strata view renders with event nodes positioned by xs (horizontal) and time (vertical)
- [ ] Resonance view renders with cluster-based ring layout
- [ ] Animated transition between views works in both directions
- [ ] Event node click → event detail panel opens
- [ ] Archetype name click (in event panel) → archetype detail panel opens
- [ ] Panel close button works
- [ ] Participant toggle shows all / individual participant views
- [ ] Participant color encoding: jessie=purple, emma=coral, steven=teal, shared=gold

### Database Operations

- [ ] `insert_event` stores all fields correctly
- [ ] `insert_cluster` stores name, centroid, is_seed (and glyph_id after S1a)
- [ ] `get_events` returns rows without embedding field
- [ ] `get_clusters` returns rows without centroid field
- [ ] `get_cluster_centroids` returns (id, centroid) tuples with parsed vectors
- [ ] `cluster_exists` returns True/False correctly

## Per-Session Regression Focus

| Session | Watch For |
|---------|-----------|
| S1a | `insert_cluster` signature change breaks `seed_clusters()`. Atomic increment changes SQL pattern — verify both from-zero and from-N cases. xs center changes shift all future event positions. |
| S1b | Dedup cap could theoretically allow re-processing if Telegram resends after eviction. Insert+increment error handling must not suppress real errors. Granola return contract change must not break `/granola` endpoint response. |
| S2 | Seeding script is additive (insert-only). Main risk: script bug causes malformed events. Verify seeded events load correctly in frontend. |
| S3 | Prompt text change only — caching logic must be untouched. Verify `should_regenerate` still works. Verify fallback path unchanged. |
| S4 | Any change to event handlers in the 48K HTML file risks breaking existing interactions. Test all panel open/close/chain paths after changes. |
