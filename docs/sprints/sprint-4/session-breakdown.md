# Sprint 4: Session Breakdown

## Session Dependency Chain

```
S1 (segmentation core) ─┐
                         ├─► S4 (Granola pipeline integration)
S2 (DB schema + layer) ──┤
                         ├─► S5 (Telegram pipeline integration)
S3 (archetype creation) ─┘
                              S4, S5 ─► S6 (truncation fix + re-seed)
```

S1, S2, S3 are independent foundations (no inter-dependencies).
S4 integrates S1 + S2 + S3 into the Granola pipeline.
S5 integrates S1 + S2 + S3 into the Telegram pipeline.
S6 depends on all prior sessions.

---

## Session 1: Segmentation Core — Prompts, Dataclass, Significance, Labels, Dedup

**Objective:** Redesign the segmentation and label prompts; extend the Segment dataclass; add significance filtering and label dedup utilities.

**Creates:** nothing
**Modifies:** `app/segmentation.py`, `app/config.py`
**Integrates:** N/A (foundation session)
**Parallelizable:** false

### Scope
- Redesign `SEGMENTATION_PROMPT`: add `significance` (float 0.0–1.0) to the JSON schema, update label instruction to marginalia register (4–8 words, proposition not tag cloud), add uniqueness instruction for labels
- Extend `Segment` dataclass: add `start_line: int`, `end_line: int`, `significance: float` fields
- Update `segment_transcript()` to parse and propagate significance, start_line, end_line from Claude response; default significance to 1.0 if missing from response
- Add `filter_by_significance(segments, threshold)` function
- Add `dedup_labels(segments)` function: finds duplicate labels, appends " (II)", " (III)" etc.
- Redesign `LABEL_PROMPT` for marginalia register, add significance score to output (return JSON `{"label": "...", "significance": 0.8}`)
- Update `generate_event_label()` to return `(label, significance)` tuple
- Add `significance_threshold: float = 0.3` to Settings

### Compaction Risk Score
| Factor | Count | Points |
|--------|-------|--------|
| New files created | 0 | 0 |
| Files modified | 2 | 2 |
| Context files (pre-flight reads) | 2 (segmentation.py, config.py) | 2 |
| New tests | ~12 | 6 |
| Complex integration wiring | 0 | 0 |
| External API debugging | 0 | 0 |
| Large single file | 0 | 0 |
| **Total** | | **10 (Medium)** |

### Tests (~12)
- Segment dataclass: new fields present and typed correctly
- Segmentation prompt: significance field parsed from response
- Segmentation prompt: missing significance field defaults to 1.0
- filter_by_significance: filters below threshold, keeps at/above
- filter_by_significance: empty input returns empty output
- filter_by_significance: all below threshold returns empty
- dedup_labels: no duplicates returns unchanged
- dedup_labels: two duplicates get " (II)" suffix on second
- dedup_labels: three duplicates get " (II)", " (III)"
- generate_event_label: returns (label, significance) tuple
- generate_event_label: label follows marginalia register (no ALL-CAPS)
- Config: significance_threshold field exists with default 0.3

---

## Session 2: DB Schema + Layer

**Objective:** Create raw_inputs table, add raw_input_id/start_line/end_line to events, implement DB functions.

**Creates:** `scripts/migrate_sprint4.sql`
**Modifies:** `app/db.py`, `scripts/init_supabase.sql`
**Integrates:** N/A (foundation session)
**Parallelizable:** false

### Scope
- DDL for `raw_inputs` table: id (UUID, PK, gen_random_uuid()), text (TEXT NOT NULL), source (TEXT NOT NULL), source_metadata (JSONB DEFAULT '{}'), created_at (TIMESTAMPTZ DEFAULT now())
- DDL for events table additions: `raw_input_id` (UUID, nullable FK → raw_inputs), `start_line` (INT, nullable), `end_line` (INT, nullable)
- Index on raw_inputs(source)
- `insert_raw_input(text, source, source_metadata)` → returns inserted row
- `get_raw_input(raw_input_id)` → returns row or None
- Update `insert_event()` signature: add optional `raw_input_id`, `start_line`, `end_line` params
- Update `scripts/init_supabase.sql` with the new table and columns (canonical schema)
- Migration script for existing production DB

### Compaction Risk Score
| Factor | Count | Points |
|--------|-------|--------|
| New files created | 1 (migrate_sprint4.sql) | 2 |
| Files modified | 2 (db.py, init_supabase.sql) | 2 |
| Context files | 2 (db.py, init_supabase.sql) | 2 |
| New tests | ~8 | 4 |
| Complex integration wiring | 0 | 0 |
| External API debugging | 0 | 0 |
| Large single file | 0 | 0 |
| **Total** | | **10 (Medium)** |

### Tests (~8)
- insert_raw_input: returns row with id, text, source, source_metadata, created_at
- insert_raw_input: source_metadata stored correctly as JSONB
- get_raw_input: returns existing row
- get_raw_input: returns None for non-existent id
- insert_event: accepts and stores raw_input_id, start_line, end_line
- insert_event: raw_input_id, start_line, end_line nullable (backward compatible)
- ensure_schema: now checks raw_inputs table
- get_events: does not include raw_input_id/start_line/end_line in default select (API contract unchanged)

---

## Session 3: Archetype Creation Core

**Objective:** Build assign_or_create_cluster() and deferred naming module.

**Creates:** `app/archetype_naming.py`
**Modifies:** `app/clustering.py`, `app/config.py`
**Integrates:** N/A (self-contained module)
**Parallelizable:** false

### Scope
- New function `assign_or_create_cluster(embedding, centroids)` in `app/clustering.py`:
  - If best similarity ≥ threshold: return (cluster_id, similarity, created=False)
  - If best similarity < threshold: call `create_dynamic_cluster(embedding)` → return (new_cluster_id, similarity, created=True)
- `create_dynamic_cluster(embedding)` in `app/clustering.py`:
  - Insert cluster with name="The Unnamed", centroid=embedding, is_seed=False, glyph_id=None
  - Return new cluster id
- `app/archetype_naming.py`:
  - `ARCHETYPE_NAMING_PROMPT`: given event labels/notes in a cluster, generate a name in the ancestral register. "The [Noun]" or "[Noun-phrase]" pattern. Use design-reference.md Copy Tone rules.
  - `generate_archetype_name(event_labels, event_notes)` → str
  - `maybe_name_cluster(cluster_id)`: check event_count ≥ archetype_naming_threshold and name == "The Unnamed"; if so, fetch cluster event labels, call generate_archetype_name, update cluster name
- Add `archetype_naming_threshold: int = 3` to Settings
- Keep existing `assign_cluster()` unchanged for backward compatibility (callers migrate in S4/S5)

### Compaction Risk Score
| Factor | Count | Points |
|--------|-------|--------|
| New files created | 1 (archetype_naming.py) | 2 |
| Files modified | 2 (clustering.py, config.py) | 2 |
| Context files | 3 (clustering.py, config.py, db.py) | 3 |
| New tests | ~10 | 5 |
| Complex integration wiring | 0 | 0 |
| External API debugging | 0 | 0 |
| Large single file | 0 | 0 |
| **Total** | | **12 (Medium)** |

### Tests (~10)
- assign_or_create_cluster: above threshold returns existing cluster, created=False
- assign_or_create_cluster: below threshold creates new cluster, created=True
- assign_or_create_cluster: at exactly threshold returns existing cluster
- create_dynamic_cluster: inserts cluster with correct fields (name, is_seed, centroid)
- generate_archetype_name: returns a name string
- generate_archetype_name: name follows register (not wellness-speak)
- maybe_name_cluster: names cluster when event_count ≥ threshold and name is "The Unnamed"
- maybe_name_cluster: no-op when event_count < threshold
- maybe_name_cluster: no-op when name is already set (not "The Unnamed")
- Config: archetype_naming_threshold field exists with default 3

---

## Session 4: Granola Pipeline + Seed Script Integration

**Objective:** Wire all Sprint 4 features into the Granola upload pipeline and batch seeding script.

**Creates:** nothing
**Modifies:** `app/granola.py`, `scripts/seed_transcript.py`
**Integrates:** S1 (Segment fields, significance filter, dedup) + S2 (raw_input storage) + S3 (assign_or_create_cluster)
**Parallelizable:** false

### Scope
- `app/granola.py` — `process_granola_upload()`:
  1. Store full transcript in raw_inputs (source="granola", metadata={speaker_map, date})
  2. Segment transcript (now returns Segment with start_line, end_line, significance)
  3. Apply dedup_labels()
  4. Apply filter_by_significance() using settings.significance_threshold
  5. Embed filtered segments
  6. For each: call assign_or_create_cluster() instead of assign_cluster()
  7. If created=True: refresh centroids list (re-fetch from DB)
  8. Insert event with raw_input_id, start_line, end_line
  9. Call maybe_name_cluster() after increment_event_count
  10. Compute xs (handle new clusters via default center)
- `scripts/seed_transcript.py`:
  - Same pipeline changes as granola.py
  - Dry-run mode: show significance scores, show which segments are filtered
  - Store transcript in raw_inputs before processing
  - Print cluster creation events in output

### Compaction Risk Score
| Factor | Count | Points |
|--------|-------|--------|
| New files created | 0 | 0 |
| Files modified | 2 (granola.py, seed_transcript.py) | 2 |
| Context files | 5 (granola.py, seed_transcript.py, segmentation.py, clustering.py, db.py) | 5 |
| New tests | ~10 | 5 |
| Complex integration wiring | yes (3+ components) | 3 |
| External API debugging | 0 | 0 |
| Large single file | 0 | 0 |
| **Total** | | **15 (High)** |

⚠️ **Score 15 — must split.**

### Split: Session 4a + Session 4b

**Session 4a: Granola Pipeline Integration**
- Modifies: `app/granola.py`
- Integrates: S1 + S2 + S3
- Context: granola.py, segmentation.py, clustering.py, db.py (4 files)
- Tests: ~6

| Factor | Count | Points |
|--------|-------|--------|
| New files created | 0 | 0 |
| Files modified | 1 | 1 |
| Context files | 4 | 4 |
| New tests | ~6 | 3 |
| Complex integration wiring | yes | 3 |
| **Total** | | **11 (Medium)** |

**Session 4b: Seed Script Integration**
- Modifies: `scripts/seed_transcript.py`
- Integrates: S1 + S2 + S3 (same pattern as 4a)
- Context: seed_transcript.py, segmentation.py, clustering.py, db.py (4 files)
- Tests: ~5

| Factor | Count | Points |
|--------|-------|--------|
| New files created | 0 | 0 |
| Files modified | 1 | 1 |
| Context files | 4 | 4 |
| New tests | ~5 | 2.5 |
| Complex integration wiring | yes | 3 |
| **Total** | | **10.5 (Medium)** |

---

## Session 5: Telegram Pipeline Integration

**Objective:** Wire raw_input storage, significance filtering, and new-cluster creation into the Telegram pipeline.

**Creates:** nothing
**Modifies:** `app/telegram.py`
**Integrates:** S1 (significance from label call) + S2 (raw_input storage) + S3 (assign_or_create_cluster)
**Parallelizable:** false

### Scope
- `process_telegram_update()` new flow:
  1. Extract message → get label + significance from `generate_event_label()`
  2. Store message in raw_inputs (source="telegram", metadata={update_id, participant, chat_id})
  3. If significance < threshold: return {processed: False, reason: "below_significance", event_id: None, raw_input_id: ...}
  4. Check duplicate (existing dedup logic)
  5. Embed text
  6. Call assign_or_create_cluster() instead of assign_cluster()
  7. Insert event with raw_input_id
  8. Call maybe_name_cluster() after increment_event_count
  9. Compute xs

### Compaction Risk Score
| Factor | Count | Points |
|--------|-------|--------|
| New files created | 0 | 0 |
| Files modified | 1 | 1 |
| Context files | 4 (telegram.py, segmentation.py, clustering.py, db.py) | 4 |
| New tests | ~6 | 3 |
| Complex integration wiring | yes (3+ components) | 3 |
| External API debugging | 0 | 0 |
| Large single file | 0 | 0 |
| **Total** | | **11 (Medium)** |

### Tests (~6)
- process_telegram_update: stores message in raw_inputs before significance check
- process_telegram_update: below-significance message stored in raw_inputs, no event created
- process_telegram_update: above-significance message creates event with raw_input_id
- process_telegram_update: below-threshold similarity creates new cluster
- process_telegram_update: calls maybe_name_cluster after event insertion
- process_telegram_update: return dict includes raw_input_id

---

## Session 6: DEF-021 Truncation Fix + Re-seed + Verification

**Objective:** Find and fix the 10,243-char truncation. Re-seed production with all Sprint 4 changes. Verify data quality improvements.

**Creates:** nothing
**Modifies:** TBD (depends on investigation — likely `app/segmentation.py` or pipeline code)
**Integrates:** all prior sessions
**Parallelizable:** false

### Scope
- Investigate: trace a known-truncated segment through the pipeline. Check max_tokens in Claude segmentation call, check if segment text extraction truncates, check Supabase field limits, check embedding input limits.
- Fix the identified limit.
- Re-seed production: clear events, re-run seed_transcript.py with Sprint 4 changes on both transcripts.
- Verify:
  - Logistics noise segments filtered out
  - Labels in marginalia register
  - No duplicate labels
  - New clusters created for below-threshold events
  - The Table no longer at 68% of events
  - Previously truncated segments now have full content
  - All transcripts stored in raw_inputs
  - Events have valid raw_input_id references

### Compaction Risk Score
| Factor | Count | Points |
|--------|-------|--------|
| New files created | 0 | 0 |
| Files modified | ~1 | 1 |
| Context files | 3 | 3 |
| New tests | ~3 | 1.5 |
| Complex integration wiring | 0 | 0 |
| External API debugging | 0 | 0 |
| Large single file | 0 | 0 |
| **Total** | | **5.5 (Low)** |

### Tests (~3)
- Regression: previously truncated segment text exceeds 10,243 chars after fix
- Truncation limit no longer present in pipeline
- (Additional tests TBD based on root cause)

---

## Summary Table

| Session | Scope | Creates | Modifies | Integrates | Score | Risk |
|---------|-------|---------|----------|------------|-------|------|
| S1 | Segmentation core | — | segmentation.py, config.py | N/A | 10 | Medium |
| S2 | DB schema + layer | migrate_sprint4.sql | db.py, init_supabase.sql | N/A | 10 | Medium |
| S3 | Archetype creation | archetype_naming.py | clustering.py, config.py | N/A | 12 | Medium |
| S4a | Granola pipeline | — | granola.py | S1+S2+S3 | 11 | Medium |
| S4b | Seed script | — | seed_transcript.py | S1+S2+S3 | 10.5 | Medium |
| S5 | Telegram pipeline | — | telegram.py | S1+S2+S3 | 11 | Medium |
| S6 | Truncation + re-seed | — | TBD | All | 5.5 | Low |

**Total sessions:** 7 (was 6, Session 4 split into 4a + 4b)
**Estimated new tests:** ~51
**Target test count:** ~217
