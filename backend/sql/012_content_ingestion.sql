-- Content ingestion (sources and items)

CREATE TABLE IF NOT EXISTS content_sources (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  kind TEXT NOT NULL, -- rss, social
  url_or_handle TEXT NOT NULL,
  filters JSONB,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_content_sources_user ON content_sources(user_id, kind);

CREATE TABLE IF NOT EXISTS content_items (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT REFERENCES content_sources(id) ON DELETE CASCADE,
  title TEXT,
  url TEXT,
  published_at TIMESTAMPTZ,
  text TEXT,
  entities JSONB,
  hash TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content_prompts (
  id BIGSERIAL PRIMARY KEY,
  item_id BIGINT REFERENCES content_items(id) ON DELETE CASCADE,
  user_id BIGINT,
  league_id BIGINT,
  prompt_text TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);


