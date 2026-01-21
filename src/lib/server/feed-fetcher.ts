import Parser from 'rss-parser';
import { Readability } from '@mozilla/readability';
import { JSDOM } from 'jsdom';
import { createArticle } from './articles';
import { updateFeedFetchStatus, getFeedById } from './feeds';
import { logger } from './logger';

const parser = new Parser({
  timeout: 10000, // 10 second timeout for feed fetching
  headers: {
    'User-Agent': 'Mozilla/5.0 (compatible; RSSReader/1.0)'
  }
});

export interface FetchedFeed {
  title: string;
  description?: string;
  link?: string;
  items: FetchedItem[];
}

export interface FetchedItem {
  guid: string;
  title: string;
  link?: string;
  author?: string;
  pubDate?: string;
  content?: string;
  contentSnippet?: string;
}

export async function fetchFeed(feedUrl: string): Promise<FetchedFeed> {
  const feed = await parser.parseURL(feedUrl);

  return {
    title: feed.title || feedUrl,
    description: feed.description,
    link: feed.link,
    items: (feed.items || []).map((item) => ({
      guid: item.guid || item.link || item.title || '',
      title: item.title || 'Untitled',
      link: item.link,
      author: item.creator || item.author,
      pubDate: item.pubDate || item.isoDate,
      content: item.content || item['content:encoded'] || item.contentSnippet,
      contentSnippet: item.contentSnippet
    }))
  };
}

export async function extractFullContent(url: string): Promise<string | null> {
  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; RSSReader/1.0)'
      },
      signal: AbortSignal.timeout(10000) // 10 second timeout
    });

    if (!response.ok) {
      return null;
    }

    const html = await response.text();
    const dom = new JSDOM(html, { url });
    const reader = new Readability(dom.window.document);
    const article = reader.parse();

    return article?.content || null;
  } catch {
    return null;
  }
}

export async function refreshFeed(
  feedId: number,
  extractContent: boolean = false
): Promise<{ added: number; errors: string[] }> {
  const feed = getFeedById(feedId);

  if (!feed) {
    return { added: 0, errors: ['Feed not found'] };
  }

  const errors: string[] = [];
  let added = 0;

  try {
    const fetchedFeed = await fetchFeed(feed.feed_url);

    // Limit to latest 50 items per feed to avoid processing too many
    const items = fetchedFeed.items.slice(0, 50);

    for (const item of items) {
      if (!item.guid) continue;

      // Only extract full content if explicitly requested (slower)
      let fullContent: string | null = null;
      if (extractContent && item.link) {
        try {
          fullContent = await extractFullContent(item.link);
        } catch {
          // Ignore extraction errors, use RSS content
        }
      }

      const article = createArticle({
        feed_id: feedId,
        guid: item.guid,
        title: item.title,
        url: item.link,
        author: item.author,
        published_at: item.pubDate ? new Date(item.pubDate).toISOString() : undefined,
        rss_content: item.content,
        full_content: fullContent || undefined
      });

      if (article) {
        added++;
      }
    }

    const now = new Date().toISOString();
    updateFeedFetchStatus(feedId, {
      last_fetched_at: now,
      last_error: null,
      error_count: 0,
      last_new_article_at: added > 0 ? now : undefined
    });

    if (added > 0) {
      logger.info('feed', `Refreshed "${feed.title}"`, { added });
    }
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    errors.push(errorMessage);

    updateFeedFetchStatus(feedId, {
      last_fetched_at: new Date().toISOString(),
      last_error: errorMessage,
      error_count: (feed.error_count || 0) + 1
    });

    logger.error('feed', `Failed to refresh "${feed.title}"`, { error: errorMessage });
  }

  return { added, errors };
}

export async function refreshAllFeeds(feedIds?: number[]): Promise<{
  total_added: number;
  feed_results: Record<number, { added: number; errors: string[] }>;
}> {
  const { getAllFeeds } = await import('./feeds');

  // If specific feedIds provided, refresh those; otherwise refresh ALL feeds
  const feeds = feedIds
    ? feedIds.map((id) => getFeedById(id)).filter((f): f is NonNullable<typeof f> => f !== null)
    : getAllFeeds();

  const feedResults: Record<number, { added: number; errors: string[] }> = {};
  let totalAdded = 0;
  let errorCount = 0;

  // Process feeds sequentially to avoid overwhelming servers
  for (const feed of feeds) {
    const result = await refreshFeed(feed.id);
    feedResults[feed.id] = result;
    totalAdded += result.added;
    if (result.errors.length > 0) errorCount++;

    // Small delay between feeds to be polite
    await new Promise((resolve) => setTimeout(resolve, 200));
  }

  return { total_added: totalAdded, feed_results: feedResults };
}

// Scheduled refresh: only refresh feeds that need it (based on TTL and priority)
export async function refreshScheduledFeeds(limit?: number): Promise<{
  total_added: number;
  feed_results: Record<number, { added: number; errors: string[] }>;
}> {
  const { getFeedsNeedingRefresh } = await import('./feeds');

  const feeds = getFeedsNeedingRefresh(limit);

  const feedResults: Record<number, { added: number; errors: string[] }> = {};
  let totalAdded = 0;
  let errorCount = 0;

  for (const feed of feeds) {
    const result = await refreshFeed(feed.id);
    feedResults[feed.id] = result;
    totalAdded += result.added;
    if (result.errors.length > 0) errorCount++;

    await new Promise((resolve) => setTimeout(resolve, 200));
  }

  return { total_added: totalAdded, feed_results: feedResults };
}
