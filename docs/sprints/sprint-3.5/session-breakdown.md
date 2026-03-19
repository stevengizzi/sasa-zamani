# Sprint 3.5 — Session Breakdown

## Dependency Chain

```
S1a (segmentation engine) → S1b (schema integration) → S2a (granola + seed pipeline) → S2b (telegram labels) → S3 (re-seed + verify)
```

Manual step between S1a and S1b: add `participants` column in Supabase SQL editor.

---

## Session S1a: Thematic Segmentation Engine

**Objective:** Create the core segmentation module that takes a raw transcript and returns thematically coherent segments with attributed speakers and LLM-generated labels.

| Column | Detail |
|--------|--------|
| Creates | `app/segmentation.py`, `tests/test_segmentation.py` |
| Modifies | — |
| Integrates | N/A (first session) |
| Parallelizable | false |

**Compaction scoring:**

| Factor | Points |
|--------|--------|
| New files: `app/segmentation.py` | +2 |
| New files: `tests/test_segmentation.py` | +2 |
| Pre-flight reads: `app/db.py`, `app/granola.py`, `docs/design-reference.md` | +3 |
| New tests: ~6 | +3 |
| External API: Claude call design (mocked in tests) | +3 |
| **Total** | **13** |

Risk: Medium — proceed with caution.

**Key design elements:**
- `segment_transcript(text: str, speaker_map: dict[str, str], default_participant: str = "shared") -> list[Segment]`
- `Segment` dataclass: `text: str`, `label: str`, `participants: list[str]`
- `generate_event_label(text: str) -> str` — standalone function for Telegram (separate small call)
- Single Claude API call per transcript, JSON response parsing
- Claude model: `claude-sonnet-4-20250514` (consistent with myth.py)
- Error handling: raise `SegmentationError` on API failure or malformed response

**Tests (~6):**
1. `test_segment_transcript_returns_segments` — mocked Claude response, verify list of Segment objects
2. `test_segment_multi_speaker_attribution` — segment with 2+ speakers has all in participants
3. `test_segment_single_speaker` — segment with 1 speaker has only that speaker
4. `test_segment_unmapped_speaker_defaults_shared` — unmapped speakers get default_participant
5. `test_segment_api_failure_raises` — Claude API error raises SegmentationError
6. `test_generate_event_label` — mocked Claude response for single-message label

---

## Session S1b: Schema Integration (participants column)

**Objective:** Add `participants` jsonb column to events table and integrate through the db/models layer.

| Column | Detail |
|--------|--------|
| Creates | — |
| Modifies | `app/db.py`, `app/models.py`, `scripts/init_supabase.sql`, `tests/test_db.py` |
| Integrates | N/A (schema layer, consumed by S2a) |
| Parallelizable | false |

**Prerequisite:** Developer must run in Supabase SQL editor before starting S1b:
```sql
ALTER TABLE events ADD COLUMN participants jsonb DEFAULT '[]';
```

**Compaction scoring:**

| Factor | Points |
|--------|--------|
| Modified: `app/db.py` | +1 |
| Modified: `app/models.py` | +1 |
| Modified: `scripts/init_supabase.sql` | +1 |
| Modified: `tests/test_db.py` | +1 |
| Pre-flight reads: `app/db.py`, `app/models.py` | +2 |
| New tests: ~3 | +1.5 |
| **Total** | **7.5** |

Risk: Low.

**Changes by file:**
- `app/db.py`: Add `participants: list[str] | None = None` param to `insert_event()`. Include in data dict when not None.
- `app/models.py`: Add `participants: list[str] | None = None` to `EventResponse`.
- `scripts/init_supabase.sql`: Add `participants jsonb DEFAULT '[]'` to events CREATE TABLE (documentation).
- `app/db.py`: Add `participants` to `get_events()` select list.

**Tests (~3):**
1. `test_insert_event_with_participants` — verify participants included in payload
2. `test_insert_event_without_participants` — verify backward compat (None → omitted)
3. `test_event_response_includes_participants` — verify EventResponse accepts participants field

---

## Session S2a: Granola + Seed Transcript Pipeline Integration

**Objective:** Replace speaker-turn parsing in both `app/granola.py` and `scripts/seed_transcript.py` with thematic segmentation from `app/segmentation.py`.

| Column | Detail |
|--------|--------|
| Creates | — |
| Modifies | `app/granola.py`, `scripts/seed_transcript.py`, `tests/test_granola.py`, `tests/test_seed_transcript.py` |
| Integrates | S1a's `app/segmentation.py` into granola.py and seed_transcript.py |
| Parallelizable | false |

**Compaction scoring:**

| Factor | Points |
|--------|--------|
| Modified: `app/granola.py` | +1 |
| Modified: `scripts/seed_transcript.py` | +1 |
| Modified: `tests/test_granola.py` | +1 |
| Modified: `tests/test_seed_transcript.py` | +1 |
| Pre-flight reads: `app/segmentation.py`, `app/granola.py`, `scripts/seed_transcript.py` | +3 |
| New tests: ~5 | +2.5 |
| Complex integration: segmentation → 2 consumers | +3 |
| **Total** | **12.5** |

Risk: Medium — proceed with caution.

**Changes by file:**
- `app/granola.py`: Remove regex-based `parse_transcript()`. Replace with call to `segment_transcript()`. Set `participant = "shared"` when `len(segment.participants) > 1`, else `segment.participants[0]`. Pass `participants=segment.participants` to `insert_event()`. Use `segment.label` as label instead of `text[:80]`.
- `scripts/seed_transcript.py`: Remove `Speaker [A-Z]:` regex and `parse_transcript()`. Replace with call to `segment_transcript()`. Same participant logic. Dry-run prints thematic segments (segmentation IS called during dry-run). `--min-length` applied post-segmentation.
- Update `--speaker-map` help text to reflect thematic segmentation context.

**Tests (~5):**
1. `test_granola_uses_segmentation` — mock `segment_transcript`, verify it's called instead of regex parsing
2. `test_granola_multi_speaker_sets_shared` — multi-participant segment produces `participant="shared"`
3. `test_granola_single_speaker_sets_name` — single-participant segment uses that name
4. `test_seed_transcript_uses_segmentation` — mock `segment_transcript`, verify integration
5. `test_seed_transcript_dry_run_calls_segmentation` — dry-run still calls segmentation but not DB

---

## Session S2b: Telegram Label Generation

**Objective:** Add Claude-generated 3-5 word labels for Telegram events, with fallback to `text[:80]` on failure.

| Column | Detail |
|--------|--------|
| Creates | — |
| Modifies | `app/telegram.py`, `tests/test_telegram.py` |
| Integrates | S1a's `generate_event_label()` function |
| Parallelizable | false |

**Compaction scoring:**

| Factor | Points |
|--------|--------|
| Modified: `app/telegram.py` | +1 |
| Modified: `tests/test_telegram.py` | +1 |
| Pre-flight reads: `app/telegram.py`, `app/segmentation.py` | +2 |
| New tests: ~3 | +1.5 |
| External API: Claude call for labels | +3 |
| **Total** | **8.5** |

Risk: Low.

**Changes by file:**
- `app/telegram.py`: In `process_telegram_update()`, after extracting message text, call `generate_event_label(text)` wrapped in try/except. On success, use returned label. On failure, fall back to `text[:80]`.
- `tests/test_telegram.py`: New tests for label generation integration.

**Tests (~3):**
1. `test_telegram_uses_llm_label` — mock `generate_event_label`, verify label from Claude used
2. `test_telegram_label_failure_falls_back` — mock failure, verify `text[:80]` used as label
3. `test_telegram_label_content` — verify label is passed to `insert_event(label=...)`

---

## Session S3: Re-Seed + Label Backfill + Verification

**Objective:** Delete existing granola events, re-seed both transcripts with thematic segmentation, backfill Telegram event labels, verify on production.

| Column | Detail |
|--------|--------|
| Creates | `scripts/backfill_labels.py` |
| Modifies | — (manual operations) |
| Integrates | S2a's updated seed_transcript.py against production |
| Parallelizable | false |

**Compaction scoring:**

| Factor | Points |
|--------|--------|
| New files: `scripts/backfill_labels.py` | +2 |
| Pre-flight reads: `scripts/seed_transcript.py` | +1 |
| New tests: ~1 | +0.5 |
| External API: live seeding + label generation | +3 |
| **Total** | **6.5** |

Risk: Low.

**Steps:**
1. Delete existing granola events: `DELETE FROM events WHERE source = 'granola'`
2. Reset cluster event_counts: `UPDATE clusters SET event_count = 0`
3. Re-seed March 17 transcript with `--date 2026-03-17`
4. Re-seed March 18 transcript with `--date 2026-03-18`
5. Run `backfill_labels.py` to update 2 existing Telegram events with LLM labels
6. Verify event counts match expectations
7. Visual verification on production URL: both views, detail panels, labels readable
8. Run `scripts/test_myth_quality.py` to check myth generation with new clusters

**`scripts/backfill_labels.py`:**
- Fetch all events where `label` matches the `text[:80]` pattern (or simply all Telegram events)
- For each, call `generate_event_label(event.note)` and update the label
- Small script, ~30 lines

**Test (~1):**
1. `test_backfill_labels_updates_event` — mock db calls and label generation

---

## Summary Table

| Session | Scope | Creates | Modifies | Score | Risk | Para |
|---------|-------|---------|----------|-------|------|------|
| S1a | Segmentation engine | `segmentation.py`, `test_segmentation.py` | — | 13 | Med | false |
| S1b | Schema integration | — | `db.py`, `models.py`, `init_supabase.sql`, `test_db.py` | 7.5 | Low | false |
| S2a | Granola + seed pipeline | — | `granola.py`, `seed_transcript.py`, `test_granola.py`, `test_seed_transcript.py` | 12.5 | Med | false |
| S2b | Telegram labels | — | `telegram.py`, `test_telegram.py` | 8.5 | Low | false |
| S3 | Re-seed + verify | `backfill_labels.py` | — | 6.5 | Low | false |
