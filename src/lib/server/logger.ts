import { getDb } from './db';

export type LogLevel = 'info' | 'warn' | 'error';
export type LogCategory = 'scheduler' | 'feed' | 'import' | 'system' | 'ttl';

export interface LogEntry {
  id: number;
  level: LogLevel;
  category: LogCategory;
  message: string;
  details: string | null;
  created_at: string;
}

// Maximum number of logs to keep
const MAX_LOGS = 1000;

/**
 * Log a message to the database and console
 */
export function log(
  level: LogLevel,
  category: LogCategory,
  message: string,
  details?: string | Record<string, unknown>
): void {
  const db = getDb();
  const detailsStr = details
    ? typeof details === 'string'
      ? details
      : JSON.stringify(details)
    : null;

  // Also log to console
  const consoleMsg = `[${category.toUpperCase()}] ${message}`;
  if (level === 'error') {
    console.error(consoleMsg, detailsStr || '');
  } else if (level === 'warn') {
    console.warn(consoleMsg, detailsStr || '');
  } else {
    console.log(consoleMsg, detailsStr || '');
  }

  // Insert into database
  try {
    db.prepare(
      `INSERT INTO logs (level, category, message, details, created_at)
       VALUES (?, ?, ?, ?, ?)`
    ).run(level, category, message, detailsStr, new Date().toISOString());

    // Cleanup old logs if we have too many
    const count = db.prepare('SELECT COUNT(*) as count FROM logs').get() as { count: number };
    if (count.count > MAX_LOGS) {
      db.prepare(
        `DELETE FROM logs WHERE id IN (
          SELECT id FROM logs ORDER BY created_at ASC LIMIT ?
        )`
      ).run(count.count - MAX_LOGS);
    }
  } catch (err) {
    console.error('Failed to write log to database:', err);
  }
}

/**
 * Convenience methods
 */
export const logger = {
  info: (category: LogCategory, message: string, details?: string | Record<string, unknown>) =>
    log('info', category, message, details),

  warn: (category: LogCategory, message: string, details?: string | Record<string, unknown>) =>
    log('warn', category, message, details),

  error: (category: LogCategory, message: string, details?: string | Record<string, unknown>) =>
    log('error', category, message, details)
};

/**
 * Get logs with optional filtering
 */
export function getLogs(options?: {
  level?: LogLevel;
  category?: LogCategory;
  limit?: number;
  offset?: number;
}): LogEntry[] {
  const db = getDb();
  const conditions: string[] = [];
  const params: (string | number)[] = [];

  if (options?.level) {
    conditions.push('level = ?');
    params.push(options.level);
  }

  if (options?.category) {
    conditions.push('category = ?');
    params.push(options.category);
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
  const limit = options?.limit ?? 100;
  const offset = options?.offset ?? 0;

  params.push(limit, offset);

  return db
    .prepare(
      `SELECT * FROM logs ${whereClause}
       ORDER BY created_at DESC
       LIMIT ? OFFSET ?`
    )
    .all(...params) as LogEntry[];
}

/**
 * Get log count for pagination
 */
export function getLogCount(options?: { level?: LogLevel; category?: LogCategory }): number {
  const db = getDb();
  const conditions: string[] = [];
  const params: string[] = [];

  if (options?.level) {
    conditions.push('level = ?');
    params.push(options.level);
  }

  if (options?.category) {
    conditions.push('category = ?');
    params.push(options.category);
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

  const result = db.prepare(`SELECT COUNT(*) as count FROM logs ${whereClause}`).get(...params) as {
    count: number;
  };

  return result.count;
}

/**
 * Get all logs for export
 */
export function getAllLogsForExport(): LogEntry[] {
  const db = getDb();
  return db.prepare('SELECT * FROM logs ORDER BY created_at DESC').all() as LogEntry[];
}

/**
 * Clear all logs
 */
export function clearLogs(): void {
  const db = getDb();
  db.prepare('DELETE FROM logs').run();
}

/**
 * Delete logs older than specified days
 */
export function deleteOldLogs(days: number): number {
  const db = getDb();
  const result = db
    .prepare("DELETE FROM logs WHERE datetime(created_at) < datetime('now', ?)")
    .run(`-${days} days`);
  return result.changes;
}
