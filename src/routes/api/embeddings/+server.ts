import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { testEmbeddingConnection } from '$lib/server/embedding-provider';
import {
  purgeAllEmbeddings,
  getEmbeddingStats,
  processNewEmbeddings,
  isEmbeddingInProgress
} from '$lib/server/embedding-job';

/**
 * GET /api/embeddings - Get embedding statistics
 */
export const GET: RequestHandler = async () => {
  const stats = getEmbeddingStats();
  return json({ ...stats, isProcessing: isEmbeddingInProgress() });
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
    // If already running, start in background and return immediately
    if (isEmbeddingInProgress()) {
      return json({ success: true, alreadyRunning: true, processed: 0, failed: 0 });
    }

    // Start processing without awaiting — return immediately so UI can poll
    processNewEmbeddings().catch(() => {});
    return json({ success: true, started: true, processed: 0, failed: 0 });
  }

  return json({ error: 'Unknown action' }, { status: 400 });
};
