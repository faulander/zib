-- RSS Reader Database Schema

CREATE TABLE IF NOT EXISTS folders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  position INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feeds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  folder_id INTEGER REFERENCES folders(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  feed_url TEXT NOT NULL UNIQUE,
  site_url TEXT,
  description TEXT,
  favicon_url TEXT,
  last_fetched_at TEXT,
  last_new_article_at TEXT,
  last_error TEXT,
  error_count INTEGER DEFAULT 0,
  fetch_priority INTEGER DEFAULT 5,
  ttl_minutes INTEGER,
  position INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
  guid TEXT NOT NULL,
  title TEXT NOT NULL,
  url TEXT,
  author TEXT,
  published_at TEXT,
  rss_content TEXT,
  full_content TEXT,
  is_read INTEGER DEFAULT 0,
  is_starred INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(feed_id, guid)
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS filters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  rule TEXT NOT NULL,
  is_enabled INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Feed statistics for adaptive TTL calculation
CREATE TABLE IF NOT EXISTS feed_statistics (
  feed_id INTEGER PRIMARY KEY REFERENCES feeds(id) ON DELETE CASCADE,

  -- Publication frequency
  avg_articles_per_day REAL DEFAULT 0,
  articles_last_7_days INTEGER DEFAULT 0,
  articles_last_30_days INTEGER DEFAULT 0,
  avg_publish_gap_hours REAL,

  -- User engagement
  total_articles_fetched INTEGER DEFAULT 0,
  total_articles_read INTEGER DEFAULT 0,
  total_articles_starred INTEGER DEFAULT 0,
  read_rate REAL DEFAULT 0,

  -- Calculated TTL
  calculated_ttl_minutes INTEGER,
  ttl_override_minutes INTEGER,
  ttl_calculation_reason TEXT,

  last_calculated_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_articles_feed_id ON articles(feed_id);
CREATE INDEX IF NOT EXISTS idx_articles_is_read ON articles(is_read);
CREATE INDEX IF NOT EXISTS idx_articles_is_starred ON articles(is_starred);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_feeds_folder_id ON feeds(folder_id);
CREATE INDEX IF NOT EXISTS idx_feeds_last_fetched ON feeds(last_fetched_at);
CREATE INDEX IF NOT EXISTS idx_feed_statistics_calculated_at ON feed_statistics(last_calculated_at);
