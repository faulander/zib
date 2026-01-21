import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { countMatchingArticles } from '$lib/server/filters';

// Test a rule without saving it
export const POST: RequestHandler = async ({ request }) => {
  const data = await request.json();

  if (!data.rule) {
    return json({ error: 'Rule is required' }, { status: 400 });
  }

  const matchCount = countMatchingArticles(data.rule);

  return json({ match_count: matchCount });
};
