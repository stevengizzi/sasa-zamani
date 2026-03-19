# Sprint 3: Session Breakdown

## Dependency Chain

```
S1a (db/clustering fixes) → S1b (pipeline fixes) → S2 (transcript seeding) → S3 (myth refinement) → S5 (verification)
                                                                                                       ↑
S4 (frontend polish) → S4f (fix contingency) ─────────────────────────────────────────────────────────┘
```

S4 is independent of S1–S3 and can run any time before S5.
S3 must follow S2 (needs real data in clusters for prompt testing).
S1b follows S1a (both touch `app/db.py`, cleaner to sequence).

---

## Session S1a: Database & Clustering Fixes

**Objective:** Fix `insert_cluster` glyph_id gap, make `increment_event_count` atomic, consolidate SEED_ARCHETYPES, adjust Gate/Silence xs centers.

**Resolves:** DEF-016, DEF-010, DEF-011, Gate/Silence xs overlap

| Column | Detail |
|--------|--------|
| Creates | — |
| Modifies | `app/db.py`, `app/clustering.py`, `scripts/seed_clusters.py` |
| Integrates | N/A |
| Parallelizable | false |

**Changes by file:**
- `app/db.py`: Add optional `glyph_id: str | None = None` param to `insert_cluster()`. Include in data dict when not None. Change `increment_event_count` from read-then-write to single `UPDATE clusters SET event_count = event_count + 1 WHERE id = ?` using RPC or raw SQL.
- `app/clustering.py`: Update `XS_CENTERS`: The Gate → 0.08, The Silence → 0.20. No other changes.
- `scripts/seed_clusters.py`: Remove duplicated `SEED_ARCHETYPES` list. Add `from app.clustering import SEED_ARCHETYPES` import. Verify script still runs.

**New tests (~7):**
- `insert_cluster` with glyph_id populates column (1)
- `insert_cluster` without glyph_id defaults to None (1)
- `seed_clusters` passes glyph_id for all 6 archetypes (1)
- `increment_event_count` atomically increments (1)
- `increment_event_count` works from count=0 (1)
- XS_CENTERS: Gate and Silence separated by ≥0.10 (1)
- `scripts/seed_clusters.py` imports from `app/clustering` successfully (1)

**Compaction Risk:**

| Factor | Points |
|--------|--------|
| Files modified: 3 | +3 |
| Pre-flight context: `app/db.py`, `app/clustering.py`, `scripts/seed_clusters.py`, `tests/test_db.py`, `tests/test_clustering.py` | +5 |
| New tests: 7 | +3.5 |
| **Total** | **11.5 (Medium)** |

---

## Session S1b: Pipeline Fixes

**Objective:** Add error handling to insert+increment sequence, cap the Telegram dedup set, verify Granola return contract.

**Resolves:** DEF-012, DEF-013, DEF-014

| Column | Detail |
|--------|--------|
| Creates | — |
| Modifies | `app/telegram.py`, `app/granola.py`, `app/db.py` (minor) |
| Integrates | N/A |
| Parallelizable | false |

**Changes by file:**
- `app/telegram.py`: Add maxlen check to `_processed_update_ids`. When set exceeds 10,000, clear oldest entries (convert to ordered structure or simple trim). Log when cap is hit.
- `app/granola.py`: Verify `process_granola_upload` returns `cluster_name` (actual name string), not `cluster_id` UUID. Current code already looks up the name — verify the field name in the return dict matches spec. Wrap the `insert_event` + `increment_event_count` sequence in try/except: if increment fails after insert succeeds, log the inconsistency with event_id and cluster_id but don't raise (the event is saved, the count is stale by 1, which self-corrects on next insert).
- `app/db.py`: No changes beyond what S1a does (increment is already atomic after S1a).

**New tests (~5):**
- Dedup set cap: adding 10,001st entry doesn't grow set beyond 10,000 (1)
- Dedup set cap: oldest entries evicted, newest preserved (1)
- Granola return contract: `cluster_name` field contains string name, not UUID (1)
- Insert+increment partial failure: insert succeeds, increment fails → event still in DB, error logged (1)
- Insert+increment partial failure: insert fails → no increment attempted (1)

**Compaction Risk:**

| Factor | Points |
|--------|--------|
| Files modified: 3 | +3 |
| Pre-flight context: `app/telegram.py`, `app/granola.py`, `app/db.py`, `tests/test_telegram.py`, `tests/test_granola.py` | +5 |
| New tests: 5 | +2.5 |
| **Total** | **10.5 (Medium)** |

---

## Session S2: Granola Transcript Seeding (FF-004)

**Objective:** Create a script that seeds the production database with both Granola transcripts. Speaker remapping, minimum segment length filtering, dry-run mode.

| Column | Detail |
|--------|--------|
| Creates | `scripts/seed_transcript.py`, `tests/test_seed_transcript.py` |
| Modifies | — |
| Integrates | Uses existing pipeline functions from `app/embedding`, `app/clustering`, `app/db` |
| Parallelizable | false |

**Script design:**
- CLI interface: `python -m scripts.seed_transcript --file docs/source/3-17-granola-transcript.md --dry-run`
- Speaker map as a dict constant per transcript (or passed as JSON arg):
  - March 17: `{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}`
  - March 18: `{"Speaker B": "emma", "Speaker C": "jessie", "Speaker F": "steven"}` — all unmapped speakers default to "shared"
- Minimum segment length: 100 characters (configurable via `--min-length`)
- Pipeline per segment: `embed_text` → `assign_cluster` (using `get_cluster_centroids`) → `insert_event` → `increment_event_count` → `compute_xs` → `update_event_xs`
- Dry-run mode: runs parsing and filtering, prints segment count per speaker and per cluster (estimated by representative text similarity), skips all DB/API calls
- Progress logging: print segment count, speaker distribution, cluster distribution after completion
- Source field: `"granola"` (matches existing convention)

**New tests (~6):**
- Speaker remapping: known speakers → correct participant (1)
- Speaker remapping: unmapped speakers → "shared" (1)
- Minimum length filter: segments < 100 chars excluded (1)
- Minimum length filter: segments ≥ 100 chars included (1)
- Dry-run mode: no DB or API calls made (1)
- End-to-end with mocked pipeline: correct number of events inserted (1)

**Compaction Risk:**

| Factor | Points |
|--------|--------|
| New files: 2 | +4 |
| Pre-flight context: `app/granola.py`, `app/clustering.py`, `app/embedding.py`, `app/db.py`, both transcripts, `tests/test_granola.py` | +7 |
| New tests: 6 | +3 |
| **Total** | **14 (High — at threshold)** |

This is at exactly 14, the split boundary. However, the script is self-contained (creates files, modifies nothing, integrates only existing functions), and the high context count is because it reads from multiple modules without modifying them. The actual implementation complexity is moderate. **Proceed with caution rather than splitting.** If compaction occurs during implementation, the session can be split at the test-writing boundary.

---

## Session S3: Myth Prompt Refinement

**Objective:** Improve `build_myth_prompt` so myth output passes the Design Brief tonal test with real cluster data. Add thin-cluster handling. Create a manual quality testing script.

| Column | Detail |
|--------|--------|
| Creates | `scripts/test_myth_quality.py` |
| Modifies | `app/myth.py` |
| Integrates | N/A |
| Parallelizable | false |

**Prompt refinement plan:**
- Expand the system-level register instructions:
  - Add: "Ancestral and exact. A scholar who has spent years inside a subject, now speaking plainly about it to someone they respect."
  - Add: "Not wellness. Not witchy. Not fantasy. Not therapy-speak."
  - Add: "This sentence could not have been written without these specific events. If it could apply to anyone's life, discard it and try again."
- Add event count to prompt context: "This constellation holds {N} moments."
- Thin-cluster path (≤2 events): shorter sentence (10–20 words), framing as emergent ("The constellation is still forming — but already...")
- Add preferred-word weighting: "Where they fit naturally, these words belong in this register: {PREFERRED_WORDS}"
- `scripts/test_myth_quality.py`: connects to production DB, fetches all clusters with events, calls `generate_myth` for each, prints cluster name + event count + myth text. Manual review tool, not an automated test.

**New tests (~3):**
- Prompt includes register guidance string (1)
- Thin-cluster variant triggers at event_count ≤ 2 (1)
- PROHIBITED_WORDS enforcement still present in prompt (1)

**Compaction Risk:**

| Factor | Points |
|--------|--------|
| New files: 1 | +2 |
| Files modified: 1 | +1 |
| Pre-flight context: `app/myth.py`, `tests/test_myth.py`, design-reference.md | +3 |
| External API (live Claude calls for quality testing) | +3 |
| New tests: 3 | +1.5 |
| **Total** | **10.5 (Medium)** |

---

## Session S4: Frontend Demo Polish

**Objective:** Add Esc key panel close, archetype→event reverse chaining, smooth fade animation on participant toggle, and a loading state for initial data fetch.

| Column | Detail |
|--------|--------|
| Creates | — |
| Modifies | `static/index.html` |
| Integrates | N/A |
| Parallelizable | false |

**Changes:**
1. **Esc key:** Add `document.addEventListener('keydown', ...)` that checks for `event.key === 'Escape'` and calls the existing panel-close function.
2. **Reverse chaining:** In the archetype detail panel rendering code, make event names/labels clickable. On click, close the archetype panel and open the event detail panel for that event. Requires finding the event object by ID or label from the fetched events array.
3. **Smooth fade:** Find the participant toggle handler. Replace instant opacity changes with CSS transitions. Add `transition: opacity 0.3s ease` to the relevant canvas-drawn elements or, if using DOM overlays, to the CSS.
4. **Loading state:** Before the first `/events` and `/clusters` responses arrive, display a centered text in the canvas area: "The pattern is still forming..." (using the empty-state language from the Design Brief). Remove once data loads.

**New tests:** 0 (Canvas-based single-file frontend; visual verification in review)

**Compaction Risk:**

| Factor | Points |
|--------|--------|
| Files modified: 1 | +1 |
| Large file (~48K) | +2 |
| Pre-flight context: `static/index.html`, `docs/design-reference.md` | +2 |
| **Total** | **5 (Low)** |

---

## Session S4f: Visual-Review Fix Contingency

**Scope:** 0.5 session budgeted for fixes discovered during S4 review. If S4 review passes clean, this session is unused.

---

## Session S5: Integration Verification + Demo Walkthrough

**Objective:** Structured end-to-end walkthrough of the complete demo flow. Document results.

| Column | Detail |
|--------|--------|
| Creates | `docs/sprints/sprint-3/demo-verification.md` |
| Modifies | Minor fixes only if critical blockers found |
| Integrates | All prior sessions |
| Parallelizable | false |

**Walkthrough checklist:**
1. Load production URL — loading state appears, then map renders with seeded data
2. Verify events from both transcripts visible (check participant colors)
3. Switch between strata and resonance views — transition animates correctly
4. Click an event node → event detail panel opens with correct data
5. Click archetype name in event panel → archetype detail panel opens (chained navigation)
6. Click event name in archetype panel → event detail panel opens (reverse chaining)
7. Press Esc → panel closes
8. Toggle individual/collective → smooth opacity fade
9. Select each participant → only their events highlighted
10. Send a Telegram message → verify it appears in the map (may require page refresh)
11. Verify myth text displays in archetype panel (non-empty, non-fallback for clusters with ≥3 events)
12. Check for console errors in browser DevTools

**No compaction scoring — this is verification, not development.**

---

## Summary Table

| Session | Scope | Creates | Modifies | Integrates | Score | Risk | Para |
|---------|-------|---------|----------|------------|-------|------|------|
| S1a | DB & clustering fixes | — | `db.py`, `clustering.py`, `seed_clusters.py` | N/A | 11.5 | Med | false |
| S1b | Pipeline fixes | — | `telegram.py`, `granola.py`, `db.py` | N/A | 10.5 | Med | false |
| S2 | Transcript seeding | `seed_transcript.py`, `test_seed_transcript.py` | — | Existing pipeline | 14 | High | false |
| S3 | Myth prompt refinement | `test_myth_quality.py` | `myth.py` | N/A | 10.5 | Med | false |
| S4 | Frontend demo polish | — | `index.html` | N/A | 5 | Low | false |
| S4f | Visual-review fixes | — | `index.html` | N/A | — | — | false |
| S5 | Integration verification | `demo-verification.md` | — | All | — | — | false |
