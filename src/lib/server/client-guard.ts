import { json } from '@sveltejs/kit';
import { CLIENT_HEADER, CLIENT_VERSION } from '$lib/client-version';

/**
 * Returns a 426 response when the request does not come from the current client
 * bundle (stale tab with old JS), otherwise null.
 */
export function rejectStaleClient(request: Request, action: string): Response | null {
  if (request.headers.get(CLIENT_HEADER) === CLIENT_VERSION) return null;
  console.warn(
    `Rejected stale-client ${action} (ua: ${request.headers.get('user-agent') ?? 'unknown'})`
  );
  return json({ error: 'Client out of date, reload the page' }, { status: 426 });
}
