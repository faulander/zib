import { getDb } from './db';
import type {
  ArticleRow,
  Article,
  ArticleFilters,
  MarkReadFilters,
  UpdateArticle
} from '$lib/types';
import { getEnabledFilters, articleMatchesFilters } from './filters';
import { getSetting } from './settings';

function rowToArticle(
  row: ArticleRow & { feed_title?: string | null; feed_favicon?: string | null; search_snippet?: string; is_feed_highlighted?: number }
): Article {
  const article: Article = {
    ...row,
    is_read: row.is_read === 1,
    is_starred: row.is_starred === 1,
    is_saved: row.is_saved === 1,
    is_feed_highlighted: row.is_feed_highlighted === 1
  };
  if (row.search_snippet) {
    (article as Article & { search_snippet: string }).search_snippet = row.search_snippet;
  }
  return article;
}

/** Sanitize user input for FTS5 MATCH syntax. */
function sanitizeSearchQuery(input: string): string {
  // Strip characters that break FTS5 syntax
  const cleaned = input.replace(/[\^{}\[\]]/g, '').trim();
  if (!cleaned) return '';
  const words = cleaned.split(/\s+/).filter(Boolean);
  if (words.length === 1) {
    // Single word: quote it and add prefix wildcard
    return '"' + words[0].replace(/"/g, '') + '"*';
  }
  // Multiple words: wrap each in double quotes for phrase matching
  return words.map(w => '"' + w.replace(/"/g, '') + '"').join(' ');
}

export function getArticles(filters: ArticleFilters = {}): Article[] {
  const db = getDb();

  const conditions: string[] = [];
  const values: (number | string)[] = [];
  const isSearch = !!filters.search?.trim();

  // FTS5 search join
  let ftsJoin = '';
  let selectExtra = '';
  if (isSearch) {
    const sanitized = sanitizeSearchQuery(filters.search!.trim());
    if (sanitized) {
      ftsJoin = 'JOIN article_search AS fts ON fts.rowid = a.id';
      conditions.push('fts.article_search MATCH ?');
      values.push(sanitized);
      selectExtra = ", snippet(article_search, 0, '<mark>', '</mark>', '...', 32) as search_snippet";
    }
  }

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

  if (filters.is_saved !== undefined) {
    conditions.push('a.is_saved = ?');
    values.push(filters.is_saved ? 1 : 0);
  }

  // Determine if highlight-based sorting is active
  const highlightMode = getSetting('highlightMode');
  const useHighlightSort = highlightMode === 'sort-first' || highlightMode === 'both';
  const hlRank = '(CASE WHEN f.is_highlighted = 1 THEN 0 ELSE 1 END)';
  // Cursor-based pagination: fetch articles older than the cursor
  if (filters.before_date) {
    if (useHighlightSort && filters.before_highlight_rank !== undefined) {
      // Three-part cursor: (highlight_rank, published_at, id)
      conditions.push(
        `(${hlRank} > ? OR (${hlRank} = ? AND a.published_at < ?) OR (${hlRank} = ? AND a.published_at = ? AND a.id < ?))`
      );
      values.push(
        filters.before_highlight_rank,
        filters.before_highlight_rank,
        filters.before_date,
        filters.before_highlight_rank,
        filters.before_date,
        filters.before_id || 0
      );
    } else {
      conditions.push('(a.published_at < ? OR (a.published_at = ? AND a.id < ?))');
      values.push(filters.before_date, filters.before_date, filters.before_id || 0);
    }
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

  // Get more articles than requested to account for filtering
  const requestedLimit = filters.limit || 50;
  // When searching, results are already filtered by relevance — no multiplier needed
  const fetchLimit = isSearch ? requestedLimit : requestedLimit * 3;

  const orderBy = useHighlightSort
    ? `ORDER BY ${hlRank}, a.published_at DESC, a.id DESC`
    : 'ORDER BY a.published_at DESC, a.id DESC';

  const articles = db
    .prepare(
      `
    SELECT a.*, f.title as feed_title, f.favicon_url as feed_favicon, f.is_highlighted as is_feed_highlighted${selectExtra}
    FROM articles a
    JOIN feeds f ON f.id = a.feed_id
    ${ftsJoin}
    ${whereClause}
    ${orderBy}
    LIMIT ?
  `
    )
    .all(...values, fetchLimit) as (ArticleRow & {
    feed_title: string;
    feed_favicon: string | null;
    is_feed_highlighted?: number;
    search_snippet?: string;
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
    SELECT a.*, f.title as feed_title, f.favicon_url as feed_favicon, f.is_highlighted as is_feed_highlighted
    FROM articles a
    JOIN feeds f ON f.id = a.feed_id
    WHERE a.id = ?
  `
    )
    .get(id) as (ArticleRow & { feed_title: string; feed_favicon: string | null; is_feed_highlighted?: number }) | undefined;

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

  if (data.is_saved !== undefined) {
    updates.push('is_saved = ?');
    values.push(data.is_saved ? 1 : 0);
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
  image_url?: string;
}): Article | null {
  const db = getDb();

  try {
    const result = db
      .prepare(
        `
      INSERT INTO articles (feed_id, guid, title, url, author, published_at, rss_content, full_content, image_url)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        data.full_content ?? null,
        data.image_url ?? null
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
  saved_total: number;
} {
  const db = getDb();
  const enabledFilters = getEnabledFilters();

  const savedTotal = db.prepare('SELECT COUNT(*) as count FROM articles WHERE is_saved = 1').get() as {
    count: number;
  };

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
      by_feed: Object.fromEntries(byFeed.map((r) => [r.feed_id, r.count])),
      saved_total: savedTotal.count
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

  return { total, by_folder: byFolder, by_feed: byFeed, saved_total: savedTotal.count };
}

export function deleteOldArticles(daysToKeep: number = 30): number {
  const db = getDb();

  const result = db
    .prepare(
      `
    DELETE FROM articles
    WHERE is_starred = 0
      AND is_saved = 0
      AND is_read = 1
      AND datetime(created_at) < datetime('now', '-' || ? || ' days')
  `
    )
    .run(daysToKeep);

  return result.changes;
}
