# Sprint 3: What This Sprint Does NOT Do

## Out of Scope

1. **Design Brief visual alignment:** No Cormorant Garamond / DM Mono typography, no river-at-night color palette, no grain overlay, no blur/atmosphere effects. The frontend retains its current visual style. Deferred to Sprint 4.
2. **FF-002 thematic segmentation:** Granola transcripts are split on speaker turns, not thematic units. Claude-based pre-processing of transcripts is a post-MVP enhancement.
3. **New input modalities:** No voice memo, no calendar integration, no manual entry UI, no new upload formats.
4. **Mobile layout:** Desktop demo only. DEF-006 remains deferred to Sprint 5.
5. **Dynamic clustering:** No HDBSCAN, no k-means, no new archetype creation. Seed clusters only (DEC-011).
6. **Moon nodes:** Unaffiliated events (below threshold) are still assigned to the nearest cluster. DEF-004 remains deferred.
7. **Truth candidates or Layer 3/4:** Myth sentences per cluster only. No accept/reject/revise mechanic, no publication frame.
8. **FF-001 Dialogue with archetypes:** No conversational mode from the archetype panel.
9. **FF-003 Tidal return notifications:** No resonance notifications, no weekly report, no Telegram bot replies.
10. **FF-005 Shareable myth cards:** No share button, no designed standalone output.
11. **Privacy flag (DEF-015):** Trust-based for three collaborators. No private flag mechanism.
12. **New archetype glyphs or glyph rendering:** DEF-016 fix populates the `glyph_id` column, but no glyph SVG rendering is added to the frontend. Glyph rendering is Sprint 4 (Design Brief alignment).

## Edge Cases to Reject

1. **Transcript segments in languages other than English:** Log and process normally. Embedding model handles multilingual input; no special handling needed.
2. **Segments that are exact duplicates across transcripts:** Process both. Dedup is by Telegram update_id only; transcript segments have no dedup mechanism. At v1 scale, duplicate events in different conversations are semantically meaningful ("they talked about this twice").
3. **Cluster with 0 events after seeding:** Should not happen (transcripts produce diverse content), but if it does, myth generation returns "The pattern is still forming" — not an error.
4. **Seeding script run twice:** The script does not check for existing events. Running it twice doubles the event count. This is operator error, not a bug. The dry-run mode mitigates this. Document in script usage notes.
5. **March 18 transcript speaker misattribution:** Granola's speaker tagging is unreliable for this transcript. Accept the mapping as best-effort. Events from misattributed speakers will have wrong participant colors but correct semantic content — clustering is unaffected.
6. **Myth prompt produces output with prohibited words despite instruction:** The `generate_myth` function does not post-validate output. If Claude ignores the instruction, the prohibited word appears in the UI. This is acceptable for v1; automated post-validation is a post-MVP enhancement.

## Scope Boundaries

- **Do NOT modify:** `app/config.py`, `app/models.py`, `app/embedding.py`, `scripts/init_supabase.sql`, `tests/conftest.py` (unless a test helper is strictly needed)
- **Do NOT optimize:** Database query performance, embedding batch size, frontend canvas rendering performance
- **Do NOT refactor:** Frontend architecture (single HTML file stays single file), backend module structure (no new modules beyond scripts)
- **Do NOT add:** New API endpoints, new database tables or columns, new Pydantic models, new external dependencies

## Interaction Boundaries

- This sprint does NOT change the behavior of: `/events` GET, `/clusters` GET, `/telegram` POST, `/granola` POST, `/myth` POST, `/health` GET response schemas. All endpoint contracts are preserved.
- This sprint does NOT affect: Railway deployment configuration, Supabase schema, GitHub Actions (if any), the Telegram bot registration or webhook URL.

## Deferred to Future Sprints

| Item | Target Sprint | DEF Reference |
|------|--------------|---------------|
| Design Brief visual alignment | Sprint 4 | — |
| Moon nodes (unaffiliated events) | Sprint 4+ | DEF-004 |
| New event arrival animation | Sprint 4+ | DEF-005 |
| Mobile layout | Sprint 5 | DEF-006 |
| Myth post-validation (automated prohibited word check) | Sprint 4+ | DEF-017 (new) |
| Transcript dedup (prevent double-seeding) | Unscheduled | DEF-018 (new) |
| SEED_ARCHETYPES fully consolidated (also in seed_transcript.py?) | Unscheduled | DEF-011 (partially resolved) |
