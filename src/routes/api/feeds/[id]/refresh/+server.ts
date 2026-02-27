import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { refreshFeed } from '$lib/server/feed-fetcher';
import { processNewEmbeddings } from '$lib/server/embedding-job';

export const POST: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid feed ID' }, { status: 400 });
  }

  const result = await refreshFeed(id);

  // Embed new articles in the background
  processNewEmbeddings().catch(() => {});

  // Return error in body but 200 status so frontend can handle it
  if (result.errors.length > 0) {
    return json({ error: result.errors[0], ...result });
  }

  return json(result);
};
