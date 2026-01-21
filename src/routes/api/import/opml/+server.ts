import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { importOPML } from '$lib/server/opml';

export const POST: RequestHandler = async ({ request }) => {
  console.log('[API] POST /api/import/opml - Starting');

  try {
    const contentType = request.headers.get('content-type') || '';
    console.log('[API] Content-Type:', contentType);

    let opmlContent: string;

    if (contentType.includes('multipart/form-data')) {
      const formData = await request.formData();
      const file = formData.get('file') as File | null;

      if (!file) {
        console.log('[API] OPML import error: No file provided');
        return json({ error: 'No file provided' }, { status: 400 });
      }

      console.log(`[API] OPML file received: ${file.name} (${file.size} bytes)`);
      opmlContent = await file.text();
    } else {
      opmlContent = await request.text();
      console.log(`[API] OPML content received: ${opmlContent.length} bytes`);
    }

    if (!opmlContent || opmlContent.trim().length === 0) {
      console.log('[API] OPML import error: Empty content');
      return json({ error: 'Empty OPML content' }, { status: 400 });
    }

    console.log('[API] Calling importOPML...');
    const result = await importOPML(opmlContent);
    console.log('[API] OPML import completed:', result);
    return json(result);
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to parse OPML';
    const stack = err instanceof Error ? err.stack : '';
    console.error('[API] OPML import error:', errorMsg);
    console.error('[API] Stack:', stack);
    return json({ error: errorMsg }, { status: 400 });
  }
};
