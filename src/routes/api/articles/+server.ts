import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getArticles, getUnreadCounts } from '$lib/server/articles';
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

  const limit = url.searchParams.get('limit');
  if (limit) filters.limit = parseInt(limit);

  // Cursor-based pagination
  const beforeDate = url.searchParams.get('before_date');
  if (beforeDate) filters.before_date = beforeDate;

  const beforeId = url.searchParams.get('before_id');
  if (beforeId) filters.before_id = parseInt(beforeId);

  // Special endpoint for counts
  if (url.searchParams.get('counts') === 'true') {
    const counts = getUnreadCounts();
    return json(counts);
  }

  const articles = getArticles(filters);
  return json(articles);
};
