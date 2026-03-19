# Sprint 4 Design Summary

**Sprint Goal:** Improve data quality across both ingestion pipelines: filter insignificant content, store all raw inputs, redesign labels for a marginalia register, deduplicate labels, implement the designed-but-unbuilt new-cluster creation path (DEC-011), and fix the 10,243-char truncation bug (DEF-021).

**Session Breakdown:**
- Session 1: Segmentation core — prompts, Segment dataclass, significance filtering, label dedup
  - Creates: nothing
  - Modifies: `app/segmentation.py`, `app/config.py`
  - Integrates: N/A
- Session 2: DB schema + layer — raw_inputs table, events FK columns, db functions
  - Creates: `scripts/migrate_sprint4.sql`
  - Modifies: `app/db.py`, `scripts/init_supabase.sql`
  - Integrates: N/A
- Session 3: Archetype creation core — assign_or_create_cluster(), naming module, maybe_name_cluster()
  - Creates: `app/archetype_naming.py`
  - Modifies: `app/clustering.py`, `app/config.py`
  - Integrates: N/A
- Session 4a: Granola pipeline integration
  - Creates: nothing
  - Modifies: `app/granola.py`
  - Integrates: S1+S2+S3
- Session 4b: Seed script integration
  - Creates: nothing
  - Modifies: `scripts/seed_transcript.py`
  - Integrates: S1+S2+S3
- Session 5: Telegram pipeline integration
  - Creates: nothing
  - Modifies: `app/telegram.py`
  - Integrates: S1+S2+S3
- Session 6: DEF-021 truncation fix + re-seed + verification
  - Creates: nothing
  - Modifies: TBD
  - Integrates: all

**Key Decisions:**
- DEC-021: Significance filtering via 0.0–1.0 score in prompts, configurable threshold (default 0.3), both pipelines
- DEC-022: raw_inputs table for all incoming data (Granola transcripts + Telegram messages); events FK back; below-threshold content stored but not promoted
- DEC-023: Deferred archetype naming — placeholder "The Unnamed" until event_count ≥ 3
- DEC-024: Post-processing label dedup with ordinal suffix " (II)", " (III)" etc.

**Scope Boundaries:**
- IN: Significance filtering, raw_inputs storage, marginalia labels, label dedup, new-cluster creation, DEF-021 fix, re-seed
- OUT: Cross-transcript label uniqueness, dynamic cluster glyphs, rolling centroid updates, frontend changes, transcript dedup, label regeneration endpoint, dynamic XS_CENTERS

**Regression Invariants:**
- /events and /clusters API contracts unchanged
- Frontend renders without errors
- Both pipelines process end-to-end
- Seed cluster centroids unchanged
- 166 existing tests pass
- New config fields have defaults (app starts without them)

**File Scope:**
- Modify: segmentation.py, config.py, db.py, clustering.py, granola.py, telegram.py, seed_transcript.py, init_supabase.sql
- Create: migrate_sprint4.sql, archetype_naming.py
- Do not modify: main.py, myth.py, embedding.py, static/index.html

**Config Changes:**
- significance_threshold (float, 0.3) → Settings.significance_threshold
- archetype_naming_threshold (int, 3) → Settings.archetype_naming_threshold

**Test Strategy:** ~51 new tests across 7 sessions. Target: ~217 total.

**Runner Compatibility:**
- Mode: Human-in-the-loop
- No runner config needed

**Escalation Criteria:**
- Degenerate significance distribution (>90% same side)
- Cluster explosion (>15 new clusters from 48 events)
- DEF-021 is a platform limit
- Archetype names fail Copy Tone test at ≥50%
- Migration script fails on production

**Doc Updates Needed:**
- project-knowledge.md, architecture.md, decision-log.md, dec-index.md, roadmap.md, risk-register.md, CLAUDE.md
