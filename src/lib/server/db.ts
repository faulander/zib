import { Database } from 'bun:sqlite';
import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

const DB_PATH = process.env.DATABASE_PATH || 'data/rss.db';

let db: Database | null = null;

export function getDb(): Database {
  if (!db) {
    // Ensure the directory exists
    const dbDir = dirname(DB_PATH);
    if (dbDir && dbDir !== '.') {
      mkdirSync(dbDir, { recursive: true });
    }
    db = new Database(DB_PATH, { create: true });
    db.run('PRAGMA journal_mode = WAL');
    db.run('PRAGMA foreign_keys = ON');
    initializeSchema(db);
  }
  return db;
}

// Inline schema to avoid file system issues in production builds
const SCHEMA = `
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
  image_url TEXT,
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

-- Application logs
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL,
  category TEXT NOT NULL,
  message TEXT NOT NULL,
  details TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_category ON logs(category);

-- Feed statistics for adaptive TTL calculation
CREATE TABLE IF NOT EXISTS feed_statistics (
  feed_id INTEGER PRIMARY KEY REFERENCES feeds(id) ON DELETE CASCADE,
  avg_articles_per_day REAL DEFAULT 0,
  articles_last_7_days INTEGER DEFAULT 0,
  articles_last_30_days INTEGER DEFAULT 0,
  avg_publish_gap_hours REAL,
  total_articles_fetched INTEGER DEFAULT 0,
  total_articles_read INTEGER DEFAULT 0,
  total_articles_starred INTEGER DEFAULT 0,
  read_rate REAL DEFAULT 0,
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
`;

function initializeSchema(database: Database): void {
  database.run(SCHEMA);

  // Run migrations for existing databases
  runMigrations(database);
}

function runMigrations(database: Database): void {
  // Migration: Add last_new_article_at column to feeds table
  const feedsColumns = database.prepare('PRAGMA table_info(feeds)').all() as { name: string }[];
  const hasLastNewArticleAt = feedsColumns.some((col) => col.name === 'last_new_article_at');

  if (!hasLastNewArticleAt) {
    database.run('ALTER TABLE feeds ADD COLUMN last_new_article_at TEXT');
    console.log('[DB] Migration: Added last_new_article_at column to feeds table');
  }

  // Migration: Add image_url column to articles table
  const articlesColumns = database.prepare('PRAGMA table_info(articles)').all() as {
    name: string;
  }[];
  const hasImageUrl = articlesColumns.some((col) => col.name === 'image_url');

  if (!hasImageUrl) {
    database.run('ALTER TABLE articles ADD COLUMN image_url TEXT');
    console.log('[DB] Migration: Added image_url column to articles table');
  }

  // Migration: Add title_only column to filters table (default 1 = title only)
  const filtersColumns = database.prepare('PRAGMA table_info(filters)').all() as {
    name: string;
  }[];
  const hasTitleOnly = filtersColumns.some((col) => col.name === 'title_only');

  if (!hasTitleOnly) {
    database.run('ALTER TABLE filters ADD COLUMN title_only INTEGER DEFAULT 1');
    console.log('[DB] Migration: Added title_only column to filters table');
  }
}

export function closeDb(): void {
  if (db) {
    db.close();
    db = null;
  }
}
