import type { RequestHandler } from './$types';
import { generateOPML } from '$lib/server/opml';

export const GET: RequestHandler = async () => {
  const opml = generateOPML('RSS Reader Export');

  return new Response(opml, {
    headers: {
      'Content-Type': 'application/xml',
      'Content-Disposition': 'attachment; filename="feeds.opml"'
    }
  });
};
