import { getDb } from './db';
import type {
  ArticleRow,
  Article,
  ArticleFilters,
  MarkReadFilters,
  UpdateArticle
} from '$lib/types';
import { getEnabledFilters, articleMatchesFilters } from './filters';

function rowToArticle(
  row: ArticleRow & { feed_title?: string | null; feed_favicon?: string | null }
): Article {
  return {
    ...row,
    is_read: row.is_read === 1,
    is_starred: row.is_starred === 1
  };
}

export function getArticles(filters: ArticleFilters = {}): Article[] {
  const db = getDb();

  const conditions: string[] = [];
  const values: (number | string)[] = [];

  if (filters.feed_id !== undefined) {
    conditions.push('a.feed_id = ?');
    values.push(filters.feed_id);
  }

  if (filters.folder_id !== undefined) {
    conditions.push('f.folder_id = ?');
    values.push(filters.folder_id);
  }

  if (filters.is_read !== undefined) {
    conditions.push('a.is_read = ?');
    values.push(filters.is_read ? 1 : 0);
  }

  if (filters.is_starred !== undefined) {
    conditions.push('a.is_starred = ?');
    values.push(filters.is_starred ? 1 : 0);
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

  // Get more articles than requested to account for filtering
  const requestedLimit = filters.limit || 50;
  const offset = filters.offset || 0;
  // Fetch extra to account for filtered articles
  const fetchLimit = requestedLimit * 3;

  const articles = db
    .prepare(
      `
    SELECT a.*, f.title as feed_title, f.favicon_url as feed_favicon
    FROM articles a
    JOIN feeds f ON f.id = a.feed_id
    ${whereClause}
    ORDER BY a.published_at DESC, a.created_at DESC
    LIMIT ? OFFSET ?
  `
    )
    .all(...values, fetchLimit, offset) as (ArticleRow & {
    feed_title: string;
    feed_favicon: string | null;
  })[];

  // Apply hide filters
  const enabledFilters = getEnabledFilters();
  const filteredArticles = articles
    .map(rowToArticle)
    .filter((article) => !articleMatchesFilters(article, enabledFilters));

  // Return only the requested limit
  return filteredArticles.slice(0, requestedLimit);
}

export function getArticleById(id: number): Article | null {
  const db = getDb();

  const article = db
    .prepare(
      `
    SELECT a.*, f.title as feed_title, f.favicon_url as feed_favicon
    FROM articles a
    JOIN feeds f ON f.id = a.feed_id
    WHERE a.id = ?
  `
    )
    .get(id) as (ArticleRow & { feed_title: string; feed_favicon: string | null }) | undefined;

  return article ? rowToArticle(article) : null;
}

export function updateArticle(id: number, data: UpdateArticle): Article | null {
  const db = getDb();

  const existing = db.prepare('SELECT * FROM articles WHERE id = ?').get(id) as
    | ArticleRow
    | undefined;

  if (!existing) {
    return null;
  }

  const updates: string[] = [];
  const values: number[] = [];

  if (data.is_read !== undefined) {
    updates.push('is_read = ?');
    values.push(data.is_read ? 1 : 0);
  }

  if (data.is_starred !== undefined) {
    updates.push('is_starred = ?');
    values.push(data.is_starred ? 1 : 0);
  }

  if (updates.length > 0) {
    values.push(id);
    db.prepare(`UPDATE articles SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  return getArticleById(id);
}

export function markArticlesRead(filters: MarkReadFilters): number {
  const db = getDb();

  const conditions: string[] = ['a.is_read = 0'];
  const values: (number | string)[] = [];

  if (filters.feed_id !== undefined) {
    conditions.push('a.feed_id = ?');
    values.push(filters.feed_id);
  }

  if (filters.folder_id !== undefined) {
    conditions.push('f.folder_id = ?');
    values.push(filters.folder_id);
  }

  if (filters.older_than) {
    let interval: string;
    switch (filters.older_than) {
      case 'day':
        interval = '-1 day';
        break;
      case 'week':
        interval = '-7 days';
        break;
      case 'month':
        interval = '-30 days';
        break;
      case 'all':
      default:
        interval = '';
    }

    if (interval) {
      conditions.push("datetime(a.published_at) < datetime('now', ?)");
      values.push(interval);
    }
  }

  const whereClause = conditions.join(' AND ');

  const result = db
    .prepare(
      `
    UPDATE articles
    SET is_read = 1
    WHERE id IN (
      SELECT a.id FROM articles a
      JOIN feeds f ON f.id = a.feed_id
      WHERE ${whereClause}
    )
  `
    )
    .run(...values);

  return result.changes;
}

export function createArticle(data: {
  feed_id: number;
  guid: string;
  title: string;
  url?: string;
  author?: string;
  published_at?: string;
  rss_content?: string;
  full_content?: string;
}): Article | null {
  const db = getDb();

  try {
    const result = db
      .prepare(
        `
      INSERT INTO articles (feed_id, guid, title, url, author, published_at, rss_content, full_content)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `
      )
      .run(
        data.feed_id,
        data.guid,
        data.title,
        data.url ?? null,
        data.author ?? null,
        data.published_at ?? null,
        data.rss_content ?? null,
        data.full_content ?? null
      );

    return getArticleById(result.lastInsertRowid as number);
  } catch (err) {
    // Unique constraint violation - article already exists
    if ((err as { code?: string }).code === 'SQLITE_CONSTRAINT_UNIQUE') {
      return null;
    }
    throw err;
  }
}

export function getUnreadCounts(): {
  total: number;
  by_folder: Record<number, number>;
  by_feed: Record<number, number>;
} {
  const db = getDb();
  const enabledFilters = getEnabledFilters();

  // If no filters, use fast SQL-only counting
  if (enabledFilters.length === 0) {
    const total = db.prepare('SELECT COUNT(*) as count FROM articles WHERE is_read = 0').get() as {
      count: number;
    };

    const byFolder = db
      .prepare(
        `
      SELECT f.folder_id, COUNT(*) as count
      FROM articles a
      JOIN feeds f ON f.id = a.feed_id
      WHERE a.is_read = 0 AND f.folder_id IS NOT NULL
      GROUP BY f.folder_id
    `
      )
      .all() as { folder_id: number; count: number }[];

    const byFeed = db
      .prepare(
        `
      SELECT feed_id, COUNT(*) as count
      FROM articles
      WHERE is_read = 0
      GROUP BY feed_id
    `
      )
      .all() as { feed_id: number; count: number }[];

    return {
      total: total.count,
      by_folder: Object.fromEntries(byFolder.map((r) => [r.folder_id, r.count])),
      by_feed: Object.fromEntries(byFeed.map((r) => [r.feed_id, r.count]))
    };
  }

  // With filters, we need to check each article
  const articles = db
    .prepare(
      `
    SELECT a.id, a.title, a.rss_content, a.full_content, a.feed_id, f.folder_id
    FROM articles a
    JOIN feeds f ON f.id = a.feed_id
    WHERE a.is_read = 0
  `
    )
    .all() as {
    id: number;
    title: string;
    rss_content: string | null;
    full_content: string | null;
    feed_id: number;
    folder_id: number | null;
  }[];

  let total = 0;
  const byFolder: Record<number, number> = {};
  const byFeed: Record<number, number> = {};

  for (const article of articles) {
    // Skip articles that match hide filters
    if (articleMatchesFilters(article, enabledFilters)) {
      continue;
    }

    total++;

    if (article.folder_id !== null) {
      byFolder[article.folder_id] = (byFolder[article.folder_id] || 0) + 1;
    }

    byFeed[article.feed_id] = (byFeed[article.feed_id] || 0) + 1;
  }

  return { total, by_folder: byFolder, by_feed: byFeed };
}

export function deleteOldArticles(daysToKeep: number = 30): number {
  const db = getDb();

  const result = db
    .prepare(
      `
    DELETE FROM articles
    WHERE is_starred = 0
      AND is_read = 1
      AND datetime(created_at) < datetime('now', '-' || ? || ' days')
  `
    )
    .run(daysToKeep);

  return result.changes;
}
