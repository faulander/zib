import { JSDOM } from 'jsdom';
import { createFolder, getAllFolders } from './folders';
import { createFeed, getFeedByUrl, getAllFeeds } from './feeds';
import type { OPMLOutline } from '$lib/types';

export function parseOPML(opmlContent: string): OPMLOutline[] {
  const dom = new JSDOM(opmlContent, { contentType: 'text/xml' });
  const doc = dom.window.document;

  const body = doc.querySelector('body');
  if (!body) {
    throw new Error('Invalid OPML: no body element found');
  }

  const outlines = body.querySelectorAll(':scope > outline');
  return Array.from(outlines).map(parseOutline);
}

function parseOutline(element: Element): OPMLOutline {
  const title = element.getAttribute('title') || element.getAttribute('text') || 'Untitled';
  const xmlUrl = element.getAttribute('xmlUrl') || undefined;
  const htmlUrl = element.getAttribute('htmlUrl') || undefined;

  const children = element.querySelectorAll(':scope > outline');
  const childOutlines = children.length > 0 ? Array.from(children).map(parseOutline) : undefined;

  return {
    title,
    xmlUrl,
    htmlUrl,
    children: childOutlines
  };
}

export interface ImportResult {
  folders_created: number;
  feeds_created: number;
  feeds_skipped: number;
  errors: string[];
}

export async function importOPML(opmlContent: string): Promise<ImportResult> {
  console.log('[OPML] Starting import...');
  const start = performance.now();

  const outlines = parseOPML(opmlContent);
  console.log(`[OPML] Parsed ${outlines.length} top-level items`);

  const result: ImportResult = {
    folders_created: 0,
    feeds_created: 0,
    feeds_skipped: 0,
    errors: []
  };

  for (const outline of outlines) {
    await processOutline(outline, null, result);
  }

  const duration = ((performance.now() - start) / 1000).toFixed(2);
  console.log(
    `[OPML] Import completed in ${duration}s: ${result.folders_created} folders, ${result.feeds_created} feeds created, ${result.feeds_skipped} skipped, ${result.errors.length} errors`
  );

  return result;
}

async function processOutline(
  outline: OPMLOutline,
  folderId: number | null,
  result: ImportResult
): Promise<void> {
  // If it has an xmlUrl, it's a feed
  if (outline.xmlUrl) {
    try {
      const existingFeed = getFeedByUrl(outline.xmlUrl);
      if (existingFeed) {
        console.log(`[OPML]   Skipped (exists): ${outline.title}`);
        result.feeds_skipped++;
        return;
      }

      createFeed({
        folder_id: folderId,
        title: outline.title,
        feed_url: outline.xmlUrl,
        site_url: outline.htmlUrl
      });

      console.log(`[OPML]   Added feed: ${outline.title}`);
      result.feeds_created++;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      console.log(`[OPML]   Error adding feed "${outline.title}": ${errorMsg}`);
      result.errors.push(`Failed to create feed "${outline.title}": ${errorMsg}`);
    }
    return;
  }

  // If it has children but no xmlUrl, it's a folder
  if (outline.children && outline.children.length > 0) {
    let newFolderId: number | null = folderId;

    try {
      const folder = createFolder({ name: outline.title });
      newFolderId = folder.id;
      console.log(`[OPML] Created folder: ${outline.title} (${outline.children.length} items)`);
      result.folders_created++;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      console.log(`[OPML] Error creating folder "${outline.title}": ${errorMsg}`);
      result.errors.push(`Failed to create folder "${outline.title}": ${errorMsg}`);
    }

    // Process children
    for (const child of outline.children) {
      await processOutline(child, newFolderId, result);
    }
  }
}

export function generateOPML(title: string = 'RSS Subscriptions'): string {
  const folders = getAllFolders();
  const feeds = getAllFeeds();

  const feedsByFolder = new Map<number | null, typeof feeds>();

  for (const feed of feeds) {
    const key = feed.folder_id;
    if (!feedsByFolder.has(key)) {
      feedsByFolder.set(key, []);
    }
    feedsByFolder.get(key)!.push(feed);
  }

  let opml = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>${escapeXml(title)}</title>
    <dateCreated>${new Date().toUTCString()}</dateCreated>
  </head>
  <body>
`;

  // Feeds without folder
  const uncategorizedFeeds = feedsByFolder.get(null) || [];
  for (const feed of uncategorizedFeeds) {
    opml += `    <outline type="rss" text="${escapeXml(feed.title)}" title="${escapeXml(feed.title)}" xmlUrl="${escapeXml(feed.feed_url)}"${feed.site_url ? ` htmlUrl="${escapeXml(feed.site_url)}"` : ''}/>\n`;
  }

  // Folders with feeds
  for (const folder of folders) {
    const folderFeeds = feedsByFolder.get(folder.id) || [];
    if (folderFeeds.length === 0) continue;

    opml += `    <outline text="${escapeXml(folder.name)}" title="${escapeXml(folder.name)}">\n`;

    for (const feed of folderFeeds) {
      opml += `      <outline type="rss" text="${escapeXml(feed.title)}" title="${escapeXml(feed.title)}" xmlUrl="${escapeXml(feed.feed_url)}"${feed.site_url ? ` htmlUrl="${escapeXml(feed.site_url)}"` : ''}/>\n`;
    }

    opml += `    </outline>\n`;
  }

  opml += `  </body>
</opml>`;

  return opml;
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}
