import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getArticleById } from '$lib/server/articles';
import { getDb } from '$lib/server/db';
import { compareTwoStrings } from '$lib/utils/similarity';
import { findSimilarByEmbedding } from '$lib/server/similarity';
import { getSetting } from '$lib/server/settings';
import type { ArticleRow, Article } from '$lib/types';

function rowToArticle(
  row: ArticleRow & { feed_title?: string | null; feed_favicon?: string | null }
): Article {
  return {
    ...row,
    is_read: row.is_read === 1,
    is_starred: row.is_starred === 1,
    is_saved: row.is_saved === 1,
    is_opened: row.is_opened === 1,
    is_sent_to_instapaper: row.is_sent_to_instapaper === 1
  };
}

export const GET: RequestHandler = async ({ params, url }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid article ID' }, { status: 400 });
  }

  const article = getArticleById(id);

  if (!article) {
    return json({ error: 'Article not found' }, { status: 404 });
  }

  const provider = getSetting('embeddingProvider');
  const useEmbeddings = provider !== 'none';
  const defaultThreshold = useEmbeddings
    ? getSetting('similarityThresholdEmbedding')
    : getSetting('similarityThreshold');

  const threshold = parseFloat(url.searchParams.get('threshold') || String(defaultThreshold));
  const timeWindowHours = parseInt(url.searchParams.get('time_window') || '48');

  const db = getDb();

  // Calculate time bounds in ISO format for SQLite comparison
  const articleDate = article.published_at ? new Date(article.published_at) : new Date();
  const minDate = new Date(articleDate.getTime() - timeWindowHours * 60 * 60 * 1000);
  const maxDate = new Date(articleDate.getTime() + timeWindowHours * 60 * 60 * 1000);

  // Get articles within the time window
  const candidates = db
    .prepare(
      `
    SELECT a.*, f.title as feed_title, f.favicon_url as feed_favicon
    FROM articles a
    JOIN feeds f ON f.id = a.feed_id
    WHERE a.id != ?
      AND a.published_at >= ?
      AND a.published_at <= ?
    ORDER BY a.published_at DESC
    LIMIT 200
  `
    )
    .all(id, minDate.toISOString(), maxDate.toISOString()) as (ArticleRow & {
    feed_title: string;
    feed_favicon: string | null;
  })[];

  // Build lookup map for candidate rows
  const candidateMap = new Map(candidates.map((c) => [c.id, c]));

  // Try embedding-based similarity first
  if (useEmbeddings) {
    const candidateIds = candidates.map((c) => c.id);
    const embeddingResults = findSimilarByEmbedding(id, candidateIds, threshold);

    if (embeddingResults.length > 0) {
      const similar: Article[] = [];
      for (const result of embeddingResults) {
        const row = candidateMap.get(result.id);
        if (row) similar.push(rowToArticle(row));
      }
      return json(similar);
    }
  }

  // Fallback to Dice coefficient
  const articleTitle = article.title.toLowerCase().trim();
  const similar: Article[] = [];

  for (const candidate of candidates) {
    const candidateTitle = candidate.title.toLowerCase().trim();
    const score = compareTwoStrings(articleTitle, candidateTitle);

    if (score >= threshold) {
      similar.push(rowToArticle(candidate));
    }
  }

  // Sort by similarity score (highest first)
  similar.sort((a, b) => {
    const scoreA = compareTwoStrings(articleTitle, a.title.toLowerCase().trim());
    const scoreB = compareTwoStrings(articleTitle, b.title.toLowerCase().trim());
    return scoreB - scoreA;
  });

  return json(similar);
};
