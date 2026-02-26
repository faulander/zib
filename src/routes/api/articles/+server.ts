import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getArticles, getUnreadCounts } from '$lib/server/articles';
import { groupSimilarArticles, flattenGroups } from '$lib/server/similarity';
import type { ArticleFilters } from '$lib/types';

export const GET: RequestHandler = async ({ url }) => {
  const filters: ArticleFilters = {};

  const feedId = url.searchParams.get('feed_id');
  if (feedId) filters.feed_id = parseInt(feedId);

  const folderId = url.searchParams.get('folder_id');
  if (folderId) filters.folder_id = parseInt(folderId);

  const isRead = url.searchParams.get('is_read');
  if (isRead !== null) filters.is_read = isRead === 'true';

  const isStarred = url.searchParams.get('is_starred');
  if (isStarred !== null) filters.is_starred = isStarred === 'true';

  const isSaved = url.searchParams.get('is_saved');
  if (isSaved !== null) filters.is_saved = isSaved === 'true';

  const limit = url.searchParams.get('limit');
  if (limit) filters.limit = parseInt(limit);

  // Cursor-based pagination
  const beforeDate = url.searchParams.get('before_date');
  if (beforeDate) filters.before_date = beforeDate;

  const beforeId = url.searchParams.get('before_id');
  if (beforeId) filters.before_id = parseInt(beforeId);

  const beforeHighlightRank = url.searchParams.get('before_highlight_rank');
  if (beforeHighlightRank !== null) filters.before_highlight_rank = parseInt(beforeHighlightRank);

  const search = url.searchParams.get('search');
  if (search) filters.search = search;

  // Special endpoint for counts
  if (url.searchParams.get('counts') === 'true') {
    const counts = getUnreadCounts();
    return json(counts);
  }

  const articles = getArticles(filters);
  const requestedLimit = filters.limit || 50;
  const hasMore = articles.length >= requestedLimit;

  // Group similar articles if requested
  const groupSimilar = url.searchParams.get('group_similar');
  const threshold = url.searchParams.get('similarity_threshold');

  if (groupSimilar === 'true') {
    const thresholdValue = threshold ? parseFloat(threshold) : 0.65;
    const groups = groupSimilarArticles(articles, thresholdValue);
    const flattenedArticles = flattenGroups(groups);
    // Return with metadata so client knows if there are more articles
    return json({ articles: flattenedArticles, hasMore });
  }

  // For backwards compatibility, also return with metadata structure
  return json({ articles, hasMore });
};
