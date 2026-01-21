import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getArticleById, updateArticle } from '$lib/server/articles';
import type { UpdateArticle } from '$lib/types';

export const GET: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid article ID' }, { status: 400 });
  }

  const article = getArticleById(id);

  if (!article) {
    return json({ error: 'Article not found' }, { status: 404 });
  }

  return json(article);
};

export const PATCH: RequestHandler = async ({ params, request }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid article ID' }, { status: 400 });
  }

  const data: UpdateArticle = await request.json();
  const article = updateArticle(id, data);

  if (!article) {
    return json({ error: 'Article not found' }, { status: 404 });
  }

  return json(article);
};
