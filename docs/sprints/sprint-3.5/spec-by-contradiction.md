# Sprint 3.5: What This Sprint Does NOT Do

## Out of Scope
1. **Dynamic clustering / centroid recomputation:** Seed cluster centroids remain tag-based. Even though thematic segments will embed better, centroids are not recomputed this sprint. Deferred — requires design decision on when/how to trigger recomputation.
2. **Myth post-validation (DEF-017):** No automated check that generated myths pass PROHIBITED_WORDS or register tests. The S3 prompt refinement is the current defense. Deferred to Sprint 4+.
3. **Transcript dedup (DEF-018):** No mechanism to prevent re-seeding the same transcript. Operator responsibility for now. Deferred to Sprint 4+.
4. **Frontend changes for `participants` display:** The `participants` array is stored and returned via API but not rendered in the detail panel. Frontend still reads `participant` (singular) for color encoding. Deferred to Sprint 4.
5. **Frontend changes of any kind:** No modifications to `static/index.html`. The data improves; the display stays the same.
6. **Myth regeneration after re-seed:** Re-seeding will change cluster contents. Myth regeneration will happen automatically on next myth request (existing `should_regenerate` logic handles this via event_count delta). No manual myth refresh step.
7. **Mobile layout:** Desktop-first, no mobile optimization.
8. **Telegram message segmentation:** Telegram messages are single-person, single-thought. They get LLM labels but NOT thematic segmentation.
9. **Granola upload via API (live) during re-seed:** The re-seed uses `scripts/seed_transcript.py`. The live `app/granola.py` pipeline is updated but not exercised during S3 verification beyond automated tests.

## Edge Cases to Reject
1. **Transcript in a language other than English:** Not handled. Segmentation prompt assumes English. Log and skip segments if Claude returns unexpected structure.
2. **Transcript with > 50 speakers:** Not a real scenario for this project (3 participants + shared). No special handling beyond the existing speaker_map mechanism.
3. **Thematic segment spanning entire transcript:** If Claude returns a single segment for the whole transcript, accept it. The `--min-length` filter is the only gate.
4. **Empty transcript (no parseable speaker turns):** `segment_transcript` should return an empty list. Callers handle empty results via existing patterns.
5. **Concurrent segmentation calls:** No rate limiting or queue. Not a concern with 3 users and batch seeding.

## Scope Boundaries
- Do NOT modify: `app/config.py`, `app/embedding.py`, `app/myth.py`, `app/clustering.py`, `app/main.py`, `static/index.html`, `tests/conftest.py`, `tests/test_myth.py`, `tests/test_clustering.py`, `tests/test_endpoints.py`
- Do NOT optimize: Segmentation prompt for token efficiency beyond basic reasonableness. Correctness first.
- Do NOT refactor: The single-file frontend. The Canvas rendering logic. The myth generation pipeline.
- Do NOT add: New API endpoints. New frontend features. New configuration files. WebSocket or real-time features.

## Interaction Boundaries
- This sprint does NOT change the behavior of: `/clusters` endpoint, `/myth` endpoint, myth generation pipeline, clustering assignment logic (`assign_cluster`), xs computation, the frontend rendering layer
- This sprint does NOT affect: The visual appearance of the Sasa Map (same views, same colors, same interactions). The shape of events changes (better labels, better segmentation), but the rendering pipeline is identical.
- This sprint DOES change: The shape of data returned by `/events` (adds `participants` field), the content of `label` fields (LLM-generated instead of `text[:80]`), the number and granularity of events per transcript (thematic segments vs speaker turns)

## Deferred to Future Sprints
| Item | Target Sprint | DEF Reference |
|------|--------------|---------------|
| Myth post-validation | Sprint 4+ | DEF-017 |
| Transcript dedup | Sprint 4+ | DEF-018 |
| Frontend display of `participants` array | Sprint 4 | — |
| Centroid recomputation from embeddings | Sprint 4+ | — |
| Dynamic clustering (HDBSCAN/k-means) | Phase 2+ | DEF-003 |
