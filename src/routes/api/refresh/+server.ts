import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { refreshAllFeeds } from '$lib/server/feed-fetcher';

export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json().catch(() => ({}));
  const feedIds = body.feed_ids as number[] | undefined;

  console.log(`[API] POST /api/refresh ${feedIds ? `(${feedIds.length} feeds)` : '(all feeds)'}`);

  const result = await refreshAllFeeds(feedIds);

  // Count errors from feed_results
  const errorCount = Object.values(result.feed_results).filter((r) => r.errors.length > 0).length;
  console.log(
    `[API] Refresh complete: ${result.total_added} new articles, ${errorCount} feeds with errors`
  );

  return json(result);
};
