-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Clusters table (created first because events references it)
CREATE TABLE clusters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  glyph_id TEXT,
  centroid VECTOR(1536),
  myth_text TEXT,
  myth_version INTEGER DEFAULT 0,
  event_count INTEGER DEFAULT 0,
  last_updated TIMESTAMPTZ DEFAULT now(),
  is_seed BOOLEAN DEFAULT false
);

-- Events table
CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ DEFAULT now(),
  event_date TIMESTAMPTZ,
  label TEXT NOT NULL,
  note TEXT,
  participant TEXT NOT NULL,
  source TEXT NOT NULL,
  embedding VECTOR(1536),
  cluster_id UUID REFERENCES clusters(id),
  xs FLOAT,
  day INTEGER
);

-- Myths history
CREATE TABLE myths (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id UUID REFERENCES clusters(id),
  text TEXT NOT NULL,
  generated_at TIMESTAMPTZ DEFAULT now(),
  event_count_at_generation INTEGER,
  version INTEGER NOT NULL
);

-- Indexes
CREATE INDEX ON events USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
CREATE INDEX ON events (participant);
CREATE INDEX ON events (cluster_id);
CREATE INDEX ON clusters USING ivfflat (centroid vector_cosine_ops) WITH (lists = 5);
