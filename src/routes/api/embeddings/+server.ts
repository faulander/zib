import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { testEmbeddingConnection } from '$lib/server/embedding-provider';
import { purgeAllEmbeddings, getEmbeddingStats, processNewEmbeddings } from '$lib/server/embedding-job';

/**
 * GET /api/embeddings - Get embedding statistics
 */
export const GET: RequestHandler = async () => {
  const stats = getEmbeddingStats();
  return json(stats);
};

/**
 * POST /api/embeddings - Actions: test, purge, process
 */
export const POST: RequestHandler = async ({ request }) => {
  const { action } = await request.json();

  if (action === 'test') {
    const result = await testEmbeddingConnection();
    return json(result);
  }

  if (action === 'purge') {
    const purged = purgeAllEmbeddings();
    return json({ success: true, purged });
  }

  if (action === 'process') {
    const result = await processNewEmbeddings();
    return json({ success: true, ...result });
  }

  return json({ error: 'Unknown action' }, { status: 400 });
};
