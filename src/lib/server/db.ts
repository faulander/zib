import Database from 'better-sqlite3';
import { readFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DB_PATH = process.env.DATABASE_PATH || 'data/rss.db';

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    // Ensure the directory exists
    const dbDir = dirname(DB_PATH);
    if (dbDir && dbDir !== '.') {
      mkdirSync(dbDir, { recursive: true });
    }
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
    initializeSchema(db);
  }
  return db;
}

function initializeSchema(database: Database.Database): void {
  const schemaPath = join(__dirname, 'schema.sql');
  const schema = readFileSync(schemaPath, 'utf-8');
  database.exec(schema);

  // Run migrations for existing databases
  runMigrations(database);
}

function runMigrations(database: Database.Database): void {
  // Migration: Add last_new_article_at column to feeds table
  const feedsColumns = database.prepare('PRAGMA table_info(feeds)').all() as { name: string }[];
  const hasLastNewArticleAt = feedsColumns.some((col) => col.name === 'last_new_article_at');

  if (!hasLastNewArticleAt) {
    database.exec('ALTER TABLE feeds ADD COLUMN last_new_article_at TEXT');
    console.log('[DB] Migration: Added last_new_article_at column to feeds table');
  }
}

export function closeDb(): void {
  if (db) {
    db.close();
    db = null;
  }
}
