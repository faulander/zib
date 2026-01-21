import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getArticleById } from '$lib/server/articles';
import { addToInstapaper, isInstapaperConfigured } from '$lib/server/instapaper';

export const POST: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid article ID' }, { status: 400 });
  }

  if (!isInstapaperConfigured()) {
    return json({ error: 'Instapaper not configured' }, { status: 503 });
  }

  const article = getArticleById(id);

  if (!article) {
    return json({ error: 'Article not found' }, { status: 404 });
  }

  if (!article.url) {
    return json({ error: 'Article has no URL' }, { status: 400 });
  }

  const result = await addToInstapaper(article.url, article.title);

  if (!result.success) {
    return json({ error: result.error }, { status: 500 });
  }

  return json(result);
};
