import Parser from 'rss-parser';
import { Readability } from '@mozilla/readability';
import { JSDOM } from 'jsdom';
import { createArticle } from './articles';
import { updateFeedFetchStatus, getFeedById } from './feeds';
import { logger } from './logger';
import { getSetting } from './settings';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type RssItem = any;

const parser = new Parser({
  timeout: 10000, // 10 second timeout for feed fetching
  headers: {
    'User-Agent': 'Mozilla/5.0 (compatible; RSSReader/1.0)'
  },
  customFields: {
    item: [
      ['media:content', 'media:content', { keepArray: true }],
      ['media:thumbnail', 'media:thumbnail'],
      ['enclosure', 'enclosure']
    ]
  }
});

/**
 * Extract image URL from various RSS item fields
 * Priority: enclosure (image) > media:content > media:thumbnail > first img in content
 */
function extractImageUrl(item: RssItem): string | undefined {
  // 1. Check enclosure (common in RSS 2.0)
  if (item.enclosure?.url && item.enclosure.type?.startsWith('image/')) {
    return item.enclosure.url;
  }

  // 2. Check media:content (Media RSS)
  if (item['media:content']) {
    const mediaContent = Array.isArray(item['media:content'])
      ? item['media:content']
      : [item['media:content']];
    for (const media of mediaContent) {
      if (media.$?.url && (!media.$.medium || media.$.medium === 'image')) {
        return media.$.url;
      }
    }
  }

  // 3. Check media:thumbnail
  if (item['media:thumbnail']?.$?.url) {
    return item['media:thumbnail'].$.url;
  }

  // 4. Extract first image from content
  const content = item.content || item['content:encoded'] || '';
  const imgMatch = content.match(/<img[^>]+src=["']([^"']+)["']/i);
  if (imgMatch?.[1]) {
    // Skip tracking pixels and tiny images
    const src = imgMatch[1];
    if (!src.includes('pixel') && !src.includes('tracker') && !src.includes('1x1')) {
      return src;
    }
  }

  return undefined;
}

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
  imageUrl?: string;
}

export async function fetchFeed(feedUrl: string): Promise<FetchedFeed> {
  // Pre-fetch to detect non-XML responses with a clear error message
  const response = await fetch(feedUrl, {
    headers: { 'User-Agent': 'Mozilla/5.0 (compatible; RSSReader/1.0)' },
    signal: AbortSignal.timeout(10000)
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch feed: HTTP ${response.status}`);
  }

  const contentType = response.headers.get('content-type') || '';
  const body = await response.text();

  if (contentType.includes('application/json') || body.trimStart().startsWith('{') || body.trimStart().startsWith('[')) {
    throw new Error('URL returned JSON instead of an RSS/Atom feed. This site may not offer a standard RSS feed at this URL.');
  }

  const feed = await parser.parseString(body);

  return {
    title: feed.title || feedUrl,
    description: feed.description,
    link: feed.link,
    items: (feed.items || []).map((item) => {
      const rssItem = item as RssItem;
      return {
        guid: item.guid || item.link || item.title || '',
        title: item.title || 'Untitled',
        link: item.link,
        author: item.creator || rssItem.author,
        pubDate: item.pubDate || item.isoDate,
        content: item.content || rssItem['content:encoded'] || item.contentSnippet,
        contentSnippet: item.contentSnippet,
        imageUrl: extractImageUrl(rssItem)
      };
    })
  };
}

export interface DiscoveredFeed {
	url: string;
	title: string;
	type: 'rss' | 'atom' | 'unknown';
}

export async function discoverFeeds(websiteUrl: string): Promise<DiscoveredFeed[]> {
	const response = await fetch(websiteUrl, {
		headers: { 'User-Agent': 'Mozilla/5.0 (compatible; RSSReader/1.0)' },
		signal: AbortSignal.timeout(10000)
	});

	if (!response.ok) return [];

	const contentType = response.headers.get('content-type') || '';
	if (!contentType.includes('html') && !contentType.includes('text')) return [];

	const html = await response.text();
	const dom = new JSDOM(html, { url: websiteUrl });
	const doc = dom.window.document;

	const feeds: DiscoveredFeed[] = [];

	// Look for <link rel="alternate"> with RSS/Atom types
	const links = doc.querySelectorAll('link[rel="alternate"]');
	for (const link of links) {
		const type = link.getAttribute('type');
		const href = link.getAttribute('href');
		const title = link.getAttribute('title');

		if (href && (type === 'application/rss+xml' || type === 'application/atom+xml')) {
			const absoluteUrl = new URL(href, websiteUrl).toString();
			feeds.push({
				url: absoluteUrl,
				title: title || absoluteUrl,
				type: type.includes('atom') ? 'atom' : 'rss'
			});
		}
	}

	if (feeds.length > 0) return feeds;

	// Fallback: try common feed paths
	const commonPaths = ['/feed', '/rss', '/atom.xml', '/feed.xml', '/rss.xml', '/index.xml', '/feed/rss', '/feed/atom'];
	const baseUrl = new URL(websiteUrl);

	for (const path of commonPaths) {
		try {
			const feedUrl = new URL(path, baseUrl.origin).toString();
			const feedRes = await fetch(feedUrl, {
				headers: { 'User-Agent': 'Mozilla/5.0 (compatible; RSSReader/1.0)' },
				signal: AbortSignal.timeout(5000),
				method: 'HEAD'
			});
			if (feedRes.ok) {
				const ct = feedRes.headers.get('content-type') || '';
				if (ct.includes('xml') || ct.includes('rss') || ct.includes('atom')) {
					try {
						const feed = await fetchFeed(feedUrl);
						feeds.push({
							url: feedUrl,
							title: feed.title || feedUrl,
							type: 'unknown'
						});
					} catch {
						// Not a valid feed, skip
					}
				}
			}
		} catch {
			// Network error for this path, continue
		}
	}

	return feeds;
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

// Maximum age (in days) for articles to be added during regular refreshes
// Articles older than this are skipped to prevent importing historical content
const MAX_ARTICLE_AGE_DAYS = 7;

export async function refreshFeed(
  feedId: number,
  extractContent: boolean = false,
  options: { skipAgeFilter?: boolean } = {}
): Promise<{ added: number; skipped: number; errors: string[] }> {
  const feed = getFeedById(feedId);

  if (!feed) {
    return { added: 0, skipped: 0, errors: ['Feed not found'] };
  }

  const errors: string[] = [];
  let added = 0;
  let skipped = 0;

  // Calculate the cutoff date for article age filtering
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - MAX_ARTICLE_AGE_DAYS);

  try {
    const fetchedFeed = await fetchFeed(feed.feed_url);

    // Limit to latest 50 items per feed to avoid processing too many
    const items = fetchedFeed.items.slice(0, 50);

    for (const item of items) {
      if (!item.guid) continue;

      // Skip articles older than the cutoff date (unless skipAgeFilter option is set or global setting is enabled)
      const globalSkipAgeFilter = getSetting('skipAgeFilter');
      if (!options.skipAgeFilter && !globalSkipAgeFilter && item.pubDate) {
        const pubDate = new Date(item.pubDate);
        if (!isNaN(pubDate.getTime()) && pubDate < cutoffDate) {
          skipped++;
          continue;
        }
      }

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
        full_content: fullContent || undefined,
        image_url: item.imageUrl
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

    if (added > 0 || skipped > 0) {
      logger.info('feed', `Refreshed "${feed.title}"`, { added, skipped });
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

  return { added, skipped, errors };
}

export async function refreshAllFeeds(feedIds?: number[]): Promise<{
  total_added: number;
  total_skipped: number;
  feed_results: Record<number, { added: number; skipped: number; errors: string[] }>;
}> {
  const { getAllFeeds } = await import('./feeds');

  // If specific feedIds provided, refresh those; otherwise refresh ALL feeds
  const feeds = feedIds
    ? feedIds.map((id) => getFeedById(id)).filter((f): f is NonNullable<typeof f> => f !== null)
    : getAllFeeds();

  const feedResults: Record<number, { added: number; skipped: number; errors: string[] }> = {};
  let totalAdded = 0;
  let totalSkipped = 0;

  // Process feeds sequentially to avoid overwhelming servers
  for (const feed of feeds) {
    const result = await refreshFeed(feed.id);
    feedResults[feed.id] = result;
    totalAdded += result.added;
    totalSkipped += result.skipped;

    // Small delay between feeds to be polite
    await new Promise((resolve) => setTimeout(resolve, 200));
  }

  return { total_added: totalAdded, total_skipped: totalSkipped, feed_results: feedResults };
}

// Scheduled refresh: only refresh feeds that need it (based on TTL and priority)
export async function refreshScheduledFeeds(limit?: number): Promise<{
  total_added: number;
  total_skipped: number;
  feed_results: Record<number, { added: number; skipped: number; errors: string[] }>;
}> {
  const { getFeedsNeedingRefresh } = await import('./feeds');

  const feeds = getFeedsNeedingRefresh(limit);

  const feedResults: Record<number, { added: number; skipped: number; errors: string[] }> = {};
  let totalAdded = 0;
  let totalSkipped = 0;

  for (const feed of feeds) {
    const result = await refreshFeed(feed.id);
    feedResults[feed.id] = result;
    totalAdded += result.added;
    totalSkipped += result.skipped;

    await new Promise((resolve) => setTimeout(resolve, 200));
  }

  return { total_added: totalAdded, total_skipped: totalSkipped, feed_results: feedResults };
}
