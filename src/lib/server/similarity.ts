import { compareTwoStrings } from '$lib/utils/similarity';
import type { Article } from '$lib/types';

export interface ArticleGroup {
  main: Article;
  similar: Article[];
}

const TIME_WINDOW_MS = 48 * 60 * 60 * 1000; // 48 hours

/**
 * Groups similar articles together based on title similarity.
 * The most recent article becomes the "main" article in each group.
 *
 * @param articles - Array of articles to group
 * @param threshold - Similarity threshold (0.0 to 1.0), default 0.65
 * @returns Array of article groups
 */
export function groupSimilarArticles(
  articles: Article[],
  threshold: number = 0.65
): ArticleGroup[] {
  if (threshold <= 0) {
    // If threshold is 0 or negative, don't group anything
    return articles.map((article) => ({ main: article, similar: [] }));
  }

  const groups: ArticleGroup[] = [];
  const used = new Set<number>();

  // Sort by date DESC (most recent first), with ID as tiebreaker for stable sort
  const sorted = [...articles].sort((a, b) => {
    const dateA = a.published_at ? new Date(a.published_at).getTime() : 0;
    const dateB = b.published_at ? new Date(b.published_at).getTime() : 0;
    if (dateB !== dateA) return dateB - dateA;
    return b.id - a.id; // Higher ID first (more recent)
  });

  for (const article of sorted) {
    if (used.has(article.id)) continue;

    const similar: Article[] = [];
    const articleDate = article.published_at ? new Date(article.published_at).getTime() : 0;
    const articleTitle = article.title.toLowerCase().trim();

    for (const candidate of sorted) {
      if (candidate.id === article.id || used.has(candidate.id)) continue;

      // Check time window (48 hours)
      const candidateDate = candidate.published_at ? new Date(candidate.published_at).getTime() : 0;

      if (Math.abs(articleDate - candidateDate) > TIME_WINDOW_MS) continue;

      // Check title similarity
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
      // Don't include similar articles in the main list - they're hidden under the main
    } else {
      result.push(group.main);
    }
  }

  return result;
}
