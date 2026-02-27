import { compareTwoStrings } from '$lib/utils/similarity';
import { getDb } from './db';
import { getSetting } from './settings';
import { cosineSimilarity, blobToEmbedding } from './embedding-provider';
import type { Article } from '$lib/types';

export interface ArticleGroup {
  main: Article;
  similar: Article[];
}

const TIME_WINDOW_MS = 48 * 60 * 60 * 1000; // 48 hours

interface EmbeddingRow {
  article_id: number;
  embedding: Buffer;
}

/**
 * Load embeddings for a set of article IDs.
 * Returns a Map of article_id -> number[] embedding.
 */
function loadEmbeddings(articleIds: number[]): Map<number, number[]> {
  if (articleIds.length === 0) return new Map();

  const db = getDb();
  const placeholders = articleIds.map(() => '?').join(',');
  const rows = db.prepare(
    `SELECT article_id, embedding FROM article_embeddings WHERE article_id IN (${placeholders})`
  ).all(...articleIds) as EmbeddingRow[];

  const map = new Map<number, number[]>();
  for (const row of rows) {
    map.set(row.article_id, blobToEmbedding(row.embedding));
  }
  return map;
}

/**
 * Groups similar articles together using embeddings (cosine similarity) when available,
 * falling back to Dice coefficient on titles.
 *
 * @param articles - Array of articles to group
 * @param threshold - Similarity threshold (0.0 to 1.0)
 * @returns Array of article groups
 */
export function groupSimilarArticles(
  articles: Article[],
  threshold: number = 0.65
): ArticleGroup[] {
  if (threshold <= 0) {
    return articles.map((article) => ({ main: article, similar: [] }));
  }

  // Try to load embeddings for articles
  const articleIds = articles.map((a) => a.id);
  const embeddings = loadEmbeddings(articleIds);

  // Use hybrid approach: embeddings where available, Dice as fallback per pair
  if (embeddings.size > 0) {
    const embeddingThreshold = getSetting('similarityThresholdEmbedding');
    return groupHybrid(articles, embeddings, embeddingThreshold, threshold);
  }

  return groupByDice(articles, threshold);
}

/**
 * Group articles using a hybrid approach: cosine similarity when both articles
 * have embeddings, Dice coefficient on titles as fallback.
 */
function groupHybrid(
  articles: Article[],
  embeddings: Map<number, number[]>,
  embeddingThreshold: number,
  diceThreshold: number
): ArticleGroup[] {
  const groups: ArticleGroup[] = [];
  const used = new Set<number>();

  for (const article of articles) {
    if (used.has(article.id)) continue;

    const similar: Article[] = [];
    const articleDate = article.published_at ? new Date(article.published_at).getTime() : 0;
    const articleEmbedding = embeddings.get(article.id);
    const articleTitle = article.title.toLowerCase().trim();

    for (const candidate of articles) {
      if (candidate.id === article.id || used.has(candidate.id)) continue;

      const candidateDate = candidate.published_at ? new Date(candidate.published_at).getTime() : 0;
      if (Math.abs(articleDate - candidateDate) > TIME_WINDOW_MS) continue;

      let isSimilar = false;
      const candidateEmbedding = embeddings.get(candidate.id);

      if (articleEmbedding && candidateEmbedding) {
        // Both have embeddings — use cosine similarity
        const score = cosineSimilarity(articleEmbedding, candidateEmbedding);
        isSimilar = score >= embeddingThreshold;
      } else {
        // At least one missing embedding — fall back to Dice
        const candidateTitle = candidate.title.toLowerCase().trim();
        const score = compareTwoStrings(articleTitle, candidateTitle);
        isSimilar = score >= diceThreshold;
      }

      if (isSimilar) {
        similar.push(candidate);
        used.add(candidate.id);
      }
    }

    used.add(article.id);
    groups.push({ main: article, similar });
  }

  return groups;
}

/**
 * Group articles using Dice coefficient on titles (original algorithm).
 */
function groupByDice(articles: Article[], threshold: number): ArticleGroup[] {
  const groups: ArticleGroup[] = [];
  const used = new Set<number>();

  for (const article of articles) {
    if (used.has(article.id)) continue;

    const similar: Article[] = [];
    const articleDate = article.published_at ? new Date(article.published_at).getTime() : 0;
    const articleTitle = article.title.toLowerCase().trim();

    for (const candidate of articles) {
      if (candidate.id === article.id || used.has(candidate.id)) continue;

      const candidateDate = candidate.published_at ? new Date(candidate.published_at).getTime() : 0;
      if (Math.abs(articleDate - candidateDate) > TIME_WINDOW_MS) continue;

      const candidateTitle = candidate.title.toLowerCase().trim();
      const score = compareTwoStrings(articleTitle, candidateTitle);

      if (score >= threshold) {
        similar.push(candidate);
        used.add(candidate.id);
      }
    }

    used.add(article.id);
    groups.push({ main: article, similar });
  }

  return groups;
}

/**
 * Find articles similar to a given article using embeddings when available.
 * Used by the per-article similar endpoint.
 */
export function findSimilarByEmbedding(
  articleId: number,
  candidateIds: number[],
  threshold: number
): { id: number; score: number }[] {
  const allIds = [articleId, ...candidateIds];
  const embeddings = loadEmbeddings(allIds);

  const articleEmbedding = embeddings.get(articleId);
  if (!articleEmbedding) return [];

  const results: { id: number; score: number }[] = [];

  for (const candidateId of candidateIds) {
    const candidateEmbedding = embeddings.get(candidateId);
    if (!candidateEmbedding) continue;

    const score = cosineSimilarity(articleEmbedding, candidateEmbedding);
    if (score >= threshold) {
      results.push({ id: candidateId, score });
    }
  }

  return results.sort((a, b) => b.score - a.score);
}

/**
 * Flattens article groups back to a flat array with similarity metadata.
 * Useful for APIs that need to return a flat list.
 *
 * @param groups - Array of article groups
 * @returns Flat array of articles with similar_count added to main articles
 */
export function flattenGroups(
  groups: ArticleGroup[]
): (Article & { similar_count?: number; similar_ids?: number[] })[] {
  const result: (Article & { similar_count?: number; similar_ids?: number[] })[] = [];

  for (const group of groups) {
    if (group.similar.length > 0) {
      result.push({
        ...group.main,
        similar_count: group.similar.length,
        similar_ids: group.similar.map((a) => a.id)
      });
    } else {
      result.push(group.main);
    }
  }

  return result;
}
