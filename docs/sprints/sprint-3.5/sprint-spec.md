# Sprint 3.5: Thematic Segmentation + LLM Labels

## Goal
Replace speaker-turn splitting with Claude-powered thematic segmentation for all transcript ingestion (batch seeding and live Granola upload). Generate meaningful LLM labels for all event types. Add multi-participant attribution to the events schema. Re-seed production with improved data quality before Edge City demo.

## Scope

### Deliverables
1. **`participants` jsonb column** on events table with full stack integration (db, models, API response)
2. **Thematic segmentation engine** (`app/segmentation.py`) that takes a raw transcript + speaker map and returns semantically coherent segments with attributed speakers and 3-5 word labels, via a single Claude API call
3. **Updated Granola pipeline** (`app/granola.py`) using thematic segmentation instead of speaker-turn regex parsing
4. **Updated batch seeding script** (`scripts/seed_transcript.py`) using thematic segmentation instead of `Speaker [A-Z]:` regex parsing
5. **Telegram label generation** — Claude-generated 3-5 word summary labels for Telegram events, with fallback to `text[:80]` on failure
6. **Production re-seed** with thematically segmented data from both Granola transcripts, plus label backfill for existing Telegram events

### Acceptance Criteria
1. **`participants` column:**
   - `events.participants` column exists as jsonb in Supabase
   - `insert_event()` accepts optional `participants: list[str] | None` parameter
   - `EventResponse` includes `participants: list[str] | None`
   - `/events` endpoint returns `participants` field in response
   - Backward compatible: existing callers without `participants` still work

2. **Thematic segmentation engine:**
   - `segment_transcript(text: str, speaker_map: dict, default_participant: str) -> list[Segment]` function exists
   - Each `Segment` contains: `text` (full segment content), `label` (3-5 word summary), `participants` (list of speaker names)
   - Segments are semantically coherent (not split mid-thought across speakers)
   - Multi-speaker segments have all contributing speakers in `participants`
   - Single Claude API call per transcript (not per segment)
   - Returns parseable structured output (JSON)
   - Handles Claude API failure gracefully (raises, does not return partial data)
   - Handles malformed Claude response gracefully (raises with descriptive error)

3. **Updated Granola pipeline:**
   - `process_granola_upload()` calls `segment_transcript()` instead of regex splitting
   - `participant` field set to "shared" when `len(participants) > 1`, else the single speaker
   - `participants` array passed to `insert_event()`
   - Pipeline error handling preserved (per-segment skip on embed/insert failure)
   - Segmentation failure fails the entire upload with descriptive error

4. **Updated batch seeding script:**
   - `seed_transcript.py` calls `segment_transcript()` instead of `Speaker [A-Z]:` regex
   - `--dry-run` still works (prints thematic segments without API/DB calls — segmentation call IS made during dry-run since it's part of parsing)
   - `--date`, `--speaker-map`, `--default-participant`, `--min-length` flags preserved
   - `--min-length` applied to thematic segments (after segmentation, before embedding)
   - Progress logging and final summary preserved

5. **Telegram label generation:**
   - `process_telegram_update()` generates a 3-5 word Claude label before inserting
   - On Claude API failure, falls back to `text[:80]` (event insertion must not be blocked)
   - Label is used as the `label` field in `insert_event()`

6. **Production re-seed:**
   - All existing `source = 'granola'` events deleted
   - Cluster `event_count` values reset to reflect remaining events
   - Both transcripts re-seeded with thematic segmentation + labels
   - 2 existing Telegram events backfilled with LLM labels
   - Visual verification on production URL confirms data quality

### Performance Benchmarks
| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Segmentation API cost per transcript | < $0.50 | Check Anthropic usage dashboard after seeding |
| Segmentation time per transcript | < 60s | Wall clock during seed run |
| Telegram label generation time | < 3s per message | Wall clock during Telegram test |

### Config Changes
No config changes in this sprint. Claude model for segmentation hardcoded in `app/segmentation.py`.

## Dependencies
- Sprint 3 complete (147 tests passing, seeded data in production)
- ANTHROPIC_API_KEY in environment (already present for myth generation)
- Manual Supabase SQL step between S1a and S1b: `ALTER TABLE events ADD COLUMN participants jsonb DEFAULT '[]'`
- Both Granola transcripts available at `docs/source/3-17-granola-transcript.md` and `docs/source/3-18-granola-transcript.md`

## Relevant Decisions
- DEC-017: Multi-participant events stored as `participant = "shared"` + `participants` jsonb array
- DEC-018: Thematic segmentation for both batch seeding and live Granola upload
- DEC-019: Segmentation prompt produces both thematic segments and labels in combined call
- DEC-005: Frontend stays HTML/JS canvas (no frontend changes this sprint)

## Relevant Risks
- RSK-001: Embedding quality — thematic segments should embed substantially better than speaker turns (larger, semantically coherent units). This sprint is expected to improve clustering quality.
- RSK-002: Myth fable risk — better-clustered events should produce more specific myths. Indirect improvement via data quality.

## Session Count Estimate
5 sessions estimated. S1a and S1b split from original Session 1 due to compaction risk (18 points pre-split). S2a and S2b split from original Session 2 due to compaction risk (16.5 points pre-split). S3 is re-seed and verification, mostly manual operations.
