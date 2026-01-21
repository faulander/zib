import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getArticleById } from '$lib/server/articles';
import { extractFullContent } from '$lib/server/feed-fetcher';
import { getDb } from '$lib/server/db';

export const POST: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid article ID' }, { status: 400 });
  }

  const article = getArticleById(id);

  if (!article) {
    return json({ error: 'Article not found' }, { status: 404 });
  }

  // Already has full content
  if (article.full_content) {
    console.log(`[API] POST /api/articles/${id}/extract - using cached content`);
    return json({ content: article.full_content, cached: true });
  }

  if (!article.url) {
    console.log(`[API] POST /api/articles/${id}/extract - no URL available`);
    return json({ error: 'Article has no URL' }, { status: 400 });
  }

  console.log(`[API] POST /api/articles/${id}/extract - fetching from ${article.url}`);

  // Extract content
  const fullContent = await extractFullContent(article.url);

  if (!fullContent) {
    console.log(`[API] POST /api/articles/${id}/extract - extraction failed, using RSS content`);
    return json({ error: 'Failed to extract content', content: article.rss_content });
  }

  // Save to database for future use
  const db = getDb();
  db.prepare('UPDATE articles SET full_content = ? WHERE id = ?').run(fullContent, id);

  console.log(`[API] POST /api/articles/${id}/extract - saved ${fullContent.length} chars`);

  return json({ content: fullContent, cached: false });
};
