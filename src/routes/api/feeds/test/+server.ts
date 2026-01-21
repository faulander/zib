import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { fetchFeed } from '$lib/server/feed-fetcher';

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
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    return json({
      success: false,
      error: errorMessage
    });
  }
};
