# Sprint 1: What This Sprint Does NOT Do

## Out of Scope
1. **POST /myth endpoint (Claude API proxy):** Deferred to Sprint 2. The myth generation layer requires the frontend to consume it — no point building it before the frontend migration.
2. **Frontend changes:** The prototype (static/index.html) is untouched. Sprint 2 migrates it to consume these endpoints.
3. **Dynamic cluster creation:** Only the 6 seed archetypes exist (DEC-011). No logic for creating new clusters, splitting clusters, or merging clusters.
4. **Authentication or authorization:** All endpoints are public. The v1 audience is three known participants.
5. **Real-time updates (WebSocket/SSE):** The frontend will poll on page load. Push-based updates are a future concern.
6. **Event deletion or editing:** Events are append-only in Sprint 1. No DELETE or PUT endpoints.
7. **Media attachments in Telegram:** Text messages only. Photos, voice messages, stickers, and documents are ignored (logged and skipped, not errored).
8. **HNSW index on pgvector:** Brute-force cosine similarity is sufficient for < 10K events. Indexing is a scaling concern.
9. **Rate limiting:** Not needed for 3 users.
10. **Admin interface or dashboard:** No management UI.
11. **Decay mechanics:** Events do not compost, fade, or change weight over time. That is Layer 3+ work.
12. **Truth candidates or myth narrative:** Layers 3 and 4 of the four-layer model are entirely out of scope.
13. **Mobile-specific handling:** No responsive considerations — this sprint is backend only.

## Edge Cases to Reject
1. **Telegram media messages (photos, voice, etc.):** Log "unsupported message type," return 200, do not store.
2. **Telegram messages from groups/channels (not direct):** Log and skip — v1 handles direct messages to the bot only.
3. **Granola transcripts in non-English languages:** Process normally — OpenAI embeddings handle multilingual input. Do NOT add language detection or translation.
4. **Events with identical text:** Store as separate events. Deduplication is not a Sprint 1 concern.
5. **Cluster centroid drift as events accumulate:** Do NOT recompute centroids in Sprint 1. Centroids are static seed values.
6. **Concurrent writes to the same event:** Not a concern at 3-user scale. No optimistic locking needed.
7. **Supabase row-level security (RLS):** Do not configure. All access goes through the service key.
8. **Telegram bot commands (/start, /help, etc.):** Return a simple text response. Do not build a command system.

## Scope Boundaries
- Do NOT modify: `static/index.html` (prototype frontend — untouched until Sprint 2)
- Do NOT modify: Any files under `docs/` (doc-sync handles updates post-sprint)
- Do NOT optimize: Embedding storage retrieval (no HNSW index, no caching of embeddings)
- Do NOT optimize: Cluster assignment (brute-force over 6 centroids is O(1) effectively)
- Do NOT refactor: The prototype's data model assumptions — Sprint 2 will adapt the frontend to whatever schema this sprint produces
- Do NOT add: Logging infrastructure beyond Python's built-in logging module
- Do NOT add: CI/CD pipeline (Railway auto-deploys from main branch)
- Do NOT add: Docker configuration (Railway handles Python deployment natively)

## Interaction Boundaries
- This sprint does NOT change the behavior of: the prototype frontend (static/index.html). It runs independently with its mocked data until Sprint 2 wires it to these endpoints.
- This sprint does NOT affect: the GitHub repo structure beyond adding the `app/` and `tests/` directories and root config files.

## Deferred to Future Sprints
| Item | Target Sprint | DEF Reference |
|------|--------------|---------------|
| POST /myth endpoint (Claude API proxy + caching) | Sprint 2 | DEF-001 |
| Frontend migration to live API data | Sprint 2 | DEF-002 |
| Dynamic cluster creation / splitting / merging | Sprint 5+ | DEF-003 |
| Centroid recomputation as events accumulate | Sprint 3+ | DEF-004 |
| Event decay / composting mechanics | Sprint 6+ | DEF-005 |
| Authentication / participant management | Sprint 4+ | DEF-006 |
| HNSW index for vector similarity at scale | Unscheduled | DEF-007 |
| Telegram media message handling (photos, voice) | Unscheduled | DEF-008 |
| Telegram group message handling | Unscheduled | DEF-009 |
