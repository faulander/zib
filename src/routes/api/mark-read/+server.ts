import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { markArticlesRead } from '$lib/server/articles';
import type { MarkReadFilters } from '$lib/types';

export const POST: RequestHandler = async ({ request }) => {
  const filters: MarkReadFilters = await request.json();

  const count = markArticlesRead(filters);

  return json({ success: true, marked_count: count });
};
