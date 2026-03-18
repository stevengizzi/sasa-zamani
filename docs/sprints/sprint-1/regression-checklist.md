# Sprint 1: Regression Checklist

Since this is Sprint 1, the existing codebase has only scaffold stubs (no implemented logic). This checklist establishes the invariants that must hold after each session and at sprint close.

## Invariants Established by This Sprint

| # | Invariant | How to Verify | Established In |
|---|-----------|---------------|----------------|
| 1 | Health endpoint returns 200 | `curl /health` returns 200 with JSON body | Session 1 |
| 2 | Health endpoint reports DB connection status | `GET /health` response includes `"database": "connected"` or `"disconnected"` | Session 2a |
| 3 | GET /events returns valid JSON array (never error on empty) | `curl /events` with empty DB returns `[]` | Session 2b |
| 4 | GET /events excludes raw embedding vectors | Response JSON has no `embedding` field | Session 2b |
| 5 | GET /clusters returns exactly 6 seed clusters | `curl /clusters` returns array of length 6 | Session 3b |
| 6 | GET /clusters excludes centroid embeddings | Response JSON has no `centroid_embedding` field | Session 2b |
| 7 | No partial writes on embedding failure | Simulate OpenAI failure; verify events table unchanged | Session 4a |
| 8 | Telegram webhook always returns 200 (even on errors) | Send malformed webhook payload; verify 200 response | Session 4a |
| 9 | Duplicate Telegram update_id does not create duplicate event | Send same update_id twice; verify single event in DB | Session 4a |
| 10 | Cluster assignment is deterministic | Embed same text twice; verify same cluster_id | Session 3b |
| 11 | All seed cluster centroids are non-null, non-zero 1536-dim vectors | Query clusters table; verify each centroid | Session 3b |
| 12 | App starts cleanly with all required env vars | `uvicorn app.main:app` exits 0 | Session 1 |
| 13 | App fails fast with clear error if required env vars missing | Remove SUPABASE_URL; verify startup error message | Session 1 |
| 14 | Participant filter is case-insensitive | `GET /events?participant=Jessie` and `?participant=jessie` return same results | Session 2b |

## Session-Cumulative Check

After each session, ALL prior invariants must still hold. The pre-flight test run catches regressions. If any prior invariant fails:

1. Do NOT proceed with the current session's work
2. Diagnose the regression
3. If it's a Category 2 bug (prior session), follow in-flight triage protocol
4. If it's caused by the current session's pre-flight changes, fix before proceeding

## Sprint Close Verification

At sprint close (after Session 4b), run the full test suite and manually verify:
- `GET /health` → 200, database connected
- `GET /events` → valid JSON array
- `GET /clusters` → 6 clusters
- `POST /telegram` with test payload → event appears in `GET /events`
- `POST /granola` with test transcript → events appear with correct participants
