import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getFilterById, updateFilter, deleteFilter, countMatchingArticles } from '$lib/server/filters';

export const GET: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid filter ID' }, { status: 400 });
  }

  const filter = getFilterById(id);

  if (!filter) {
    return json({ error: 'Filter not found' }, { status: 404 });
  }

  return json(filter);
};

export const PUT: RequestHandler = async ({ params, request }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid filter ID' }, { status: 400 });
  }

  const data = await request.json();

  console.log(`[API] PUT /api/filters/${id} - Updating filter`);

  const filter = updateFilter(id, {
    name: data.name,
    rule: data.rule,
    is_enabled: data.is_enabled
  });

  if (!filter) {
    return json({ error: 'Filter not found' }, { status: 404 });
  }

  // Count matching articles for feedback
  const matchCount = countMatchingArticles(filter.rule);

  return json({ ...filter, match_count: matchCount });
};

export const DELETE: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid filter ID' }, { status: 400 });
  }

  console.log(`[API] DELETE /api/filters/${id}`);

  const deleted = deleteFilter(id);

  if (!deleted) {
    return json({ error: 'Filter not found' }, { status: 404 });
  }

  return json({ success: true });
};
