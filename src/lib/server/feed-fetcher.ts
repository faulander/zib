import Parser from 'rss-parser';
import { Readability } from '@mozilla/readability';
import { JSDOM } from 'jsdom';
import { createArticle } from './articles';
import { updateFeedFetchStatus, getFeedById } from './feeds';

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
  console.log(`[Feed] Fetching: ${feedUrl}`);
  const start = performance.now();

  const feed = await parser.parseURL(feedUrl);
  const duration = (performance.now() - start).toFixed(0);

  console.log(`[Feed] Fetched ${feed.items?.length || 0} items from ${feedUrl} (${duration}ms)`);

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
  console.log(`[Extract] Fetching content from: ${url}`);
  const start = performance.now();

  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; RSSReader/1.0)'
      },
      signal: AbortSignal.timeout(10000) // 10 second timeout
    });

    if (!response.ok) {
      console.log(`[Extract] Failed (HTTP ${response.status}): ${url}`);
      return null;
    }

    const html = await response.text();
    const dom = new JSDOM(html, { url });
    const reader = new Readability(dom.window.document);
    const article = reader.parse();

    const duration = (performance.now() - start).toFixed(0);
    const contentLength = article?.content?.length || 0;
    console.log(`[Extract] Extracted ${contentLength} chars from ${url} (${duration}ms)`);

    return article?.content || null;
  } catch (err) {
    const duration = (performance.now() - start).toFixed(0);
    console.log(
      `[Extract] Error after ${duration}ms for ${url}:`,
      err instanceof Error ? err.message : err
    );
    return null;
  }
}

export async function refreshFeed(
  feedId: number,
  extractContent: boolean = false
): Promise<{ added: number; errors: string[] }> {
  const feed = getFeedById(feedId);

  if (!feed) {
    console.log(`[Refresh] Feed ${feedId} not found`);
    return { added: 0, errors: ['Feed not found'] };
  }

  console.log(`[Refresh] Starting: ${feed.title}`);
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

    updateFeedFetchStatus(feedId, {
      last_fetched_at: new Date().toISOString(),
      last_error: null,
      error_count: 0
    });

    console.log(`[Refresh] Done: ${feed.title} (+${added} new)`);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    errors.push(errorMessage);

    updateFeedFetchStatus(feedId, {
      last_fetched_at: new Date().toISOString(),
      last_error: errorMessage,
      error_count: (feed.error_count || 0) + 1
    });

    console.log(`[Refresh] Error: ${feed.title} - ${errorMessage}`);
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

  console.log(`[RefreshAll] Starting refresh of ${feeds.length} feeds`);
  const start = performance.now();

  const feedResults: Record<number, { added: number; errors: string[] }> = {};
  let totalAdded = 0;
  let errorCount = 0;

  // Process feeds sequentially to avoid overwhelming servers
  for (let i = 0; i < feeds.length; i++) {
    const feed = feeds[i];
    console.log(`[RefreshAll] (${i + 1}/${feeds.length}) ${feed.title}`);

    const result = await refreshFeed(feed.id);
    feedResults[feed.id] = result;
    totalAdded += result.added;
    if (result.errors.length > 0) errorCount++;

    // Small delay between feeds to be polite
    await new Promise((resolve) => setTimeout(resolve, 200));
  }

  const duration = ((performance.now() - start) / 1000).toFixed(1);
  console.log(
    `[RefreshAll] Completed in ${duration}s: ${totalAdded} new articles, ${errorCount} errors`
  );

  return { total_added: totalAdded, feed_results: feedResults };
}

// Scheduled refresh: only refresh feeds that need it (based on TTL and priority)
export async function refreshScheduledFeeds(limit?: number): Promise<{
  total_added: number;
  feed_results: Record<number, { added: number; errors: string[] }>;
}> {
  const { getFeedsNeedingRefresh } = await import('./feeds');

  const feeds = getFeedsNeedingRefresh(limit);

  console.log(`[ScheduledRefresh] Starting refresh of ${feeds.length} feeds`);
  const start = performance.now();

  const feedResults: Record<number, { added: number; errors: string[] }> = {};
  let totalAdded = 0;
  let errorCount = 0;

  for (let i = 0; i < feeds.length; i++) {
    const feed = feeds[i];
    console.log(`[ScheduledRefresh] (${i + 1}/${feeds.length}) ${feed.title}`);

    const result = await refreshFeed(feed.id);
    feedResults[feed.id] = result;
    totalAdded += result.added;
    if (result.errors.length > 0) errorCount++;

    await new Promise((resolve) => setTimeout(resolve, 200));
  }

  const duration = ((performance.now() - start) / 1000).toFixed(1);
  console.log(
    `[ScheduledRefresh] Completed in ${duration}s: ${totalAdded} new articles, ${errorCount} errors`
  );

  return { total_added: totalAdded, feed_results: feedResults };
}
