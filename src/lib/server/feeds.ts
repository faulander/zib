import { getDb } from './db';
import type { FeedRow, Feed, CreateFeed, UpdateFeed } from '$lib/types';

export function getAllFeeds(): Feed[] {
  const db = getDb();

  const feeds = db
    .prepare(
      `
    SELECT f.*,
           fo.name as folder_name,
           COALESCE(SUM(CASE WHEN a.is_read = 0 THEN 1 ELSE 0 END), 0) as unread_count
    FROM feeds f
    LEFT JOIN folders fo ON fo.id = f.folder_id
    LEFT JOIN articles a ON a.feed_id = f.id
    GROUP BY f.id
    ORDER BY f.position, f.title
  `
    )
    .all() as (FeedRow & { folder_name: string | null; unread_count: number })[];

  return feeds;
}

export function getFeedsByFolder(folderId: number | null): Feed[] {
  const db = getDb();

  const query =
    folderId === null
      ? `
      SELECT f.*,
             COALESCE(SUM(CASE WHEN a.is_read = 0 THEN 1 ELSE 0 END), 0) as unread_count
      FROM feeds f
      LEFT JOIN articles a ON a.feed_id = f.id
      WHERE f.folder_id IS NULL
      GROUP BY f.id
      ORDER BY f.position, f.title
    `
      : `
      SELECT f.*,
             COALESCE(SUM(CASE WHEN a.is_read = 0 THEN 1 ELSE 0 END), 0) as unread_count
      FROM feeds f
      LEFT JOIN articles a ON a.feed_id = f.id
      WHERE f.folder_id = ?
      GROUP BY f.id
      ORDER BY f.position, f.title
    `;

  const feeds = folderId === null ? db.prepare(query).all() : db.prepare(query).all(folderId);

  return feeds as Feed[];
}

export function getFeedById(id: number): Feed | null {
  const db = getDb();

  const feed = db
    .prepare(
      `
    SELECT f.*,
           fo.name as folder_name,
           COALESCE(SUM(CASE WHEN a.is_read = 0 THEN 1 ELSE 0 END), 0) as unread_count
    FROM feeds f
    LEFT JOIN folders fo ON fo.id = f.folder_id
    LEFT JOIN articles a ON a.feed_id = f.id
    WHERE f.id = ?
    GROUP BY f.id
  `
    )
    .get(id) as (FeedRow & { folder_name: string | null; unread_count: number }) | undefined;

  return feed || null;
}

export function getFeedByUrl(feedUrl: string): Feed | null {
  const db = getDb();

  const feed = db.prepare('SELECT * FROM feeds WHERE feed_url = ?').get(feedUrl) as
    | FeedRow
    | undefined;

  return feed || null;
}

export function createFeed(data: CreateFeed): Feed {
  const db = getDb();

  const maxPosition = db
    .prepare(
      'SELECT COALESCE(MAX(position), -1) + 1 as next_position FROM feeds WHERE folder_id IS ?'
    )
    .get(data.folder_id ?? null) as { next_position: number };

  const result = db
    .prepare(
      `
    INSERT INTO feeds (folder_id, title, feed_url, site_url, description, position)
    VALUES (?, ?, ?, ?, ?, ?)
  `
    )
    .run(
      data.folder_id ?? null,
      data.title,
      data.feed_url,
      data.site_url ?? null,
      data.description ?? null,
      maxPosition.next_position
    );

  return getFeedById(result.lastInsertRowid as number)!;
}

export function updateFeed(id: number, data: UpdateFeed): Feed | null {
  const db = getDb();

  const existing = db.prepare('SELECT * FROM feeds WHERE id = ?').get(id) as FeedRow | undefined;

  if (!existing) {
    return null;
  }

  const updates: string[] = [];
  const values: (string | number | null)[] = [];

  if (data.folder_id !== undefined) {
    updates.push('folder_id = ?');
    values.push(data.folder_id);
  }

  if (data.title !== undefined) {
    updates.push('title = ?');
    values.push(data.title);
  }

  if (data.feed_url !== undefined) {
    updates.push('feed_url = ?');
    values.push(data.feed_url);
  }

  if (data.site_url !== undefined) {
    updates.push('site_url = ?');
    values.push(data.site_url);
  }

  if (data.description !== undefined) {
    updates.push('description = ?');
    values.push(data.description);
  }

  if (data.position !== undefined) {
    updates.push('position = ?');
    values.push(data.position);
  }

  if (updates.length > 0) {
    values.push(id);
    db.prepare(`UPDATE feeds SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  return getFeedById(id);
}

export function updateFeedFetchStatus(
  id: number,
  status: {
    last_fetched_at: string;
    last_error?: string | null;
    error_count?: number;
    last_new_article_at?: string;
  }
): void {
  const db = getDb();

  if (status.last_new_article_at) {
    db.prepare(
      `
      UPDATE feeds
      SET last_fetched_at = ?, last_error = ?, error_count = COALESCE(?, error_count), last_new_article_at = ?
      WHERE id = ?
    `
    ).run(
      status.last_fetched_at,
      status.last_error ?? null,
      status.error_count ?? null,
      status.last_new_article_at,
      id
    );
  } else {
    db.prepare(
      `
      UPDATE feeds
      SET last_fetched_at = ?, last_error = ?, error_count = COALESCE(?, error_count)
      WHERE id = ?
    `
    ).run(status.last_fetched_at, status.last_error ?? null, status.error_count ?? null, id);
  }
}

export function deleteFeed(id: number): boolean {
  const db = getDb();
  const result = db.prepare('DELETE FROM feeds WHERE id = ?').run(id);
  return result.changes > 0;
}

export function getFeedsWithErrors(): Feed[] {
  const db = getDb();

  const feeds = db
    .prepare(
      `
    SELECT f.*, fo.name as folder_name
    FROM feeds f
    LEFT JOIN folders fo ON fo.id = f.folder_id
    WHERE f.last_error IS NOT NULL AND f.last_error != ''
    ORDER BY f.error_count DESC, f.title
  `
    )
    .all() as (FeedRow & { folder_name: string | null })[];

  return feeds;
}

export function clearFeedError(id: number): void {
  const db = getDb();
  db.prepare('UPDATE feeds SET last_error = NULL, error_count = 0 WHERE id = ?').run(id);
}

export function getFeedsNeedingRefresh(limit?: number): FeedRow[] {
  const db = getDb();

  // Priority-based refresh using adaptive TTL:
  // 1. Use ttl_override_minutes if set (user manual override)
  // 2. Fall back to calculated_ttl_minutes from feed_statistics
  // 3. Fall back to ttl_minutes from feed settings
  // 4. Default to 30 minutes
  const query = `
    SELECT f.* FROM feeds f
    LEFT JOIN feed_statistics fs ON fs.feed_id = f.id
    WHERE f.last_fetched_at IS NULL
       OR datetime(f.last_fetched_at, '+' ||
          COALESCE(fs.ttl_override_minutes, fs.calculated_ttl_minutes, f.ttl_minutes, 30)
          || ' minutes') < datetime('now')
    ORDER BY
      f.error_count ASC,
      f.fetch_priority DESC,
      f.last_fetched_at ASC NULLS FIRST
    ${limit ? 'LIMIT ?' : ''}
  `;

  const feeds = limit
    ? (db.prepare(query).all(limit) as FeedRow[])
    : (db.prepare(query).all() as FeedRow[]);

  return feeds;
}


export function reorderFeeds(items: { id: number; position: number; folder_id?: number | null }[]): void {
  const db = getDb();
  const stmt = db.prepare('UPDATE feeds SET position = ?, folder_id = COALESCE(?, folder_id) WHERE id = ?');
  const tx = db.transaction(() => {
    for (const item of items) {
      stmt.run(item.position, item.folder_id ?? null, item.id);
    }
  });
  tx();
}