import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { importOPML } from '$lib/server/opml';
import { logger } from '$lib/server/logger';

export const POST: RequestHandler = async ({ request }) => {
  const contentType = request.headers.get('content-type') || '';

  let opmlContent: string;

  if (contentType.includes('multipart/form-data')) {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;

    if (!file) {
      return json({ error: 'No file provided' }, { status: 400 });
    }

    opmlContent = await file.text();
  } else {
    opmlContent = await request.text();
  }

  if (!opmlContent || opmlContent.trim().length === 0) {
    return json({ error: 'Empty OPML content' }, { status: 400 });
  }

  try {
    const result = await importOPML(opmlContent);
    logger.info('import', `OPML import completed`, {
      feeds: result.feeds_created,
      folders: result.folders_created,
      skipped: result.feeds_skipped
    });
    return json(result);
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to parse OPML';
    logger.error('import', `OPML import failed`, { error: errorMsg });
    return json({ error: errorMsg }, { status: 400 });
  }
};
