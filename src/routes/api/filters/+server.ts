import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllFilters, createFilter, countMatchingArticles } from '$lib/server/filters';

export const GET: RequestHandler = async () => {
  const filters = getAllFilters();
  return json(filters);
};

export const POST: RequestHandler = async ({ request }) => {
  const data = await request.json();

  if (!data.name || !data.rule) {
    return json({ error: 'Name and rule are required' }, { status: 400 });
  }

  console.log(`[API] POST /api/filters - Creating filter: ${data.name}`);

  const filter = createFilter({
    name: data.name,
    rule: data.rule,
    is_enabled: data.is_enabled !== false
  });

  // Count matching articles for feedback
  const matchCount = countMatchingArticles(filter.rule);
  console.log(`[API] Filter "${filter.name}" matches ${matchCount} articles`);

  return json({ ...filter, match_count: matchCount });
};
