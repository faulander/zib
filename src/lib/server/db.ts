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
  is_opened INTEGER DEFAULT 0,
  is_sent_to_instapaper INTEGER DEFAULT 0,
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
  total_articles_engaged INTEGER DEFAULT 0,
  read_rate REAL DEFAULT 0,
  engagement_rate REAL DEFAULT 0,
  calculated_ttl_minutes INTEGER,
  ttl_override_minutes INTEGER,
  ttl_calculation_reason TEXT,
  last_calculated_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Article embeddings for semantic similarity
CREATE TABLE IF NOT EXISTS article_embeddings (
  article_id INTEGER PRIMARY KEY REFERENCES articles(id) ON DELETE CASCADE,
  embedding BLOB NOT NULL,
  model TEXT NOT NULL,
  dimensions INTEGER NOT NULL,
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

CREATE VIRTUAL TABLE IF NOT EXISTS article_search USING fts5(
	title,
	rss_content,
	full_content,
	author,
	content=articles,
	content_rowid=id
);

CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
	INSERT INTO article_search(rowid, title, rss_content, full_content, author)
	VALUES (new.id, new.title, new.rss_content, new.full_content, new.author);
END;

CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
	INSERT INTO article_search(article_search, rowid, title, rss_content, full_content, author)
	VALUES('delete', old.id, old.title, old.rss_content, old.full_content, old.author);
END;

CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
	INSERT INTO article_search(article_search, rowid, title, rss_content, full_content, author)
	VALUES('delete', old.id, old.title, old.rss_content, old.full_content, old.author);
	INSERT INTO article_search(rowid, title, rss_content, full_content, author)
	VALUES (new.id, new.title, new.rss_content, new.full_content, new.author);
END;
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

  // Migration: Add is_saved column to articles table
  const articlesCols = database.prepare('PRAGMA table_info(articles)').all() as { name: string }[];
  const hasIsSaved = articlesCols.some((col) => col.name === 'is_saved');
  if (!hasIsSaved) {
  	database.run('ALTER TABLE articles ADD COLUMN is_saved INTEGER DEFAULT 0');
  	database.run('CREATE INDEX IF NOT EXISTS idx_articles_is_saved ON articles(is_saved)');
  	console.log('[DB] Migration: Added is_saved column to articles table');
  }

  // Migration: Add is_opened column to articles table
  const hasIsOpened = articlesCols.some((col) => col.name === 'is_opened');
  if (!hasIsOpened) {
    database.run('ALTER TABLE articles ADD COLUMN is_opened INTEGER DEFAULT 0');
    database.run('CREATE INDEX IF NOT EXISTS idx_articles_is_opened ON articles(is_opened)');
    console.log('[DB] Migration: Added is_opened column to articles table');
  }

  // Migration: Add is_sent_to_instapaper column to articles table
  const hasIsSentToInstapaper = articlesCols.some((col) => col.name === 'is_sent_to_instapaper');
  if (!hasIsSentToInstapaper) {
    database.run('ALTER TABLE articles ADD COLUMN is_sent_to_instapaper INTEGER DEFAULT 0');
    console.log('[DB] Migration: Added is_sent_to_instapaper column to articles table');
  }

  // Migration: Add engagement columns to feed_statistics
  const feedStatsColumns = database.prepare('PRAGMA table_info(feed_statistics)').all() as { name: string }[];
  const hasEngagementRate = feedStatsColumns.some((col) => col.name === 'engagement_rate');
  if (!hasEngagementRate) {
    database.run('ALTER TABLE feed_statistics ADD COLUMN total_articles_engaged INTEGER DEFAULT 0');
    database.run('ALTER TABLE feed_statistics ADD COLUMN engagement_rate REAL DEFAULT 0');
    console.log('[DB] Migration: Added engagement columns to feed_statistics table');
  }

  // Migration: Add is_highlighted column to feeds table
  const hasIsHighlighted = feedsColumns.some((col) => col.name === 'is_highlighted');
  if (!hasIsHighlighted) {
    database.run('ALTER TABLE feeds ADD COLUMN is_highlighted INTEGER DEFAULT 0');
    console.log('[DB] Migration: Added is_highlighted column to feeds table');
  }

  // Migration: Populate FTS5 search index for existing articles
  try {
    const ftsCount = database.prepare('SELECT COUNT(*) as count FROM article_search').get() as { count: number };
    const articlesCount = database.prepare('SELECT COUNT(*) as count FROM articles').get() as { count: number };
    if (ftsCount.count === 0 && articlesCount.count > 0) {
      database.run('INSERT INTO article_search(rowid, title, rss_content, full_content, author) SELECT id, title, rss_content, full_content, author FROM articles');
      console.log('[DB] Migration: Populated FTS5 search index');
    }
  } catch {
    // FTS table might not exist yet on first run, will be created by schema
  }
}

export function closeDb(): void {
  if (db) {
    db.close();
    db = null;
  }
}
