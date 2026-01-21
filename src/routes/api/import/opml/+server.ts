import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { importOPML } from '$lib/server/opml';

export const POST: RequestHandler = async ({ request }) => {
  console.log('[API] POST /api/import/opml');

  const contentType = request.headers.get('content-type') || '';

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

  try {
    const result = await importOPML(opmlContent);
    return json(result);
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to parse OPML';
    console.log(`[API] OPML import error: ${errorMsg}`);
    return json({ error: errorMsg }, { status: 400 });
  }
};
