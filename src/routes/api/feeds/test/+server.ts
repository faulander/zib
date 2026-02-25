import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { fetchFeed, discoverFeeds } from '$lib/server/feed-fetcher';

export const POST: RequestHandler = async ({ request }) => {
  const { url } = await request.json();

  if (!url || typeof url !== 'string') {
    return json({ error: 'URL is required' }, { status: 400 });
  }

  try {
    const feed = await fetchFeed(url);
    return json({
      success: true,
      title: feed.title,
      description: feed.description,
      itemCount: feed.items.length
    });
  } catch (err) {
    // Feed parsing failed — try auto-discovery
    try {
      const discovered = await discoverFeeds(url);
      if (discovered.length > 0) {
        return json({
          success: false,
          discovered_feeds: discovered,
          message: `Not a feed URL, but found ${discovered.length} feed(s) on this site`
        });
      }
    } catch {
      // Discovery also failed, return original error
    }

    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    return json({
      success: false,
      error: errorMessage
    });
  }
};
