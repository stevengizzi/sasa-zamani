-- Sprint 4 migration: raw_inputs table + events FK columns
-- Run in Supabase SQL editor before pipeline integration sessions.

-- raw_inputs table
CREATE TABLE IF NOT EXISTS raw_inputs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text TEXT NOT NULL,
  source TEXT NOT NULL,
  source_metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS raw_inputs_source_idx ON raw_inputs (source);

-- Add FK columns to events (nullable — existing rows have no raw_input_id)
ALTER TABLE events ADD COLUMN IF NOT EXISTS raw_input_id UUID REFERENCES raw_inputs(id);
ALTER TABLE events ADD COLUMN IF NOT EXISTS start_line INTEGER;
ALTER TABLE events ADD COLUMN IF NOT EXISTS end_line INTEGER;
