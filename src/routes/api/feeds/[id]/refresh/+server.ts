import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { refreshFeed } from '$lib/server/feed-fetcher';

export const POST: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid feed ID' }, { status: 400 });
  }

  const result = await refreshFeed(id);

  if (result.errors.length > 0 && result.added === 0) {
    return json({ error: result.errors[0], ...result }, { status: 500 });
  }

  return json(result);
};
