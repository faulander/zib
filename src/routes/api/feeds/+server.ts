import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllFeeds, createFeed, getFeedByUrl } from '$lib/server/feeds';
import { fetchFeed } from '$lib/server/feed-fetcher';
import type { CreateFeed } from '$lib/types';

export const GET: RequestHandler = async ({ url }) => {
  const folderId = url.searchParams.get('folder_id');

  // If folder_id is provided, filter by it (handled in getAllFeeds)
  const feeds = getAllFeeds();

  if (folderId !== null) {
    const id = folderId === 'null' ? null : parseInt(folderId);
    return json(feeds.filter((f) => f.folder_id === id));
  }

  return json(feeds);
};

export const POST: RequestHandler = async ({ request }) => {
  const data: CreateFeed = await request.json();

  if (!data.feed_url || typeof data.feed_url !== 'string') {
    return json({ error: 'Feed URL is required' }, { status: 400 });
  }

  // Check if feed already exists
  const existing = getFeedByUrl(data.feed_url);
  if (existing) {
    return json({ error: 'Feed already exists', feed: existing }, { status: 409 });
  }

  // Try to fetch feed metadata if title not provided
  if (!data.title) {
    try {
      const feedData = await fetchFeed(data.feed_url);
      data.title = feedData.title || data.feed_url;
      data.site_url = feedData.link || data.site_url;
      data.description = feedData.description || data.description;
    } catch {
      data.title = data.feed_url;
    }
  }

  const feed = createFeed(data);
  return json(feed, { status: 201 });
};
