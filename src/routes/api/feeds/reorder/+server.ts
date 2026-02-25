import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { reorderFeeds } from '$lib/server/feeds';

export const POST: RequestHandler = async ({ request }) => {
	const { items } = await request.json();
	if (!Array.isArray(items)) {
		return json({ error: 'items array required' }, { status: 400 });
	}
	reorderFeeds(items);
	return json({ success: true });
};
