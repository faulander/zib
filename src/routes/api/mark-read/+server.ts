import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { markArticleIdsRead, markArticlesRead } from '$lib/server/articles';
import type { MarkReadFilters } from '$lib/types';
import { rejectStaleClient } from '$lib/server/client-guard';

export const POST: RequestHandler = async ({ request }) => {
  const body: MarkReadFilters & { ids?: unknown } = await request.json();
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return json({ error: 'Invalid mark-read request' }, { status: 400 });
  }

  if ('ids' in body) {
    const ids = body.ids;
    if (
      !Array.isArray(ids) ||
      ids.length === 0 ||
      ids.length > 1000 ||
      !ids.every((id) => Number.isSafeInteger(id) && id > 0)
    ) {
      return json({ error: 'Invalid article IDs' }, { status: 400 });
    }
    const rejected = rejectStaleClient(request, 'POST /api/mark-read ids');
    if (rejected) return rejected;
    return json({ success: true, marked_count: markArticleIdsRead(ids) });
  }

  return json({ success: true, marked_count: markArticlesRead(body) });
};
