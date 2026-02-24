import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getFilterById, getRecentMatchingArticles } from '$lib/server/filters';

export const GET: RequestHandler = async ({ params, url }) => {
	const id = parseInt(params.id);

	if (isNaN(id)) {
		return json({ error: 'Invalid filter ID' }, { status: 400 });
	}

	const filter = getFilterById(id);

	if (!filter) {
		return json({ error: 'Filter not found' }, { status: 404 });
	}

	const limit = parseInt(url.searchParams.get('limit') || '10');
	const matches = getRecentMatchingArticles(filter.rule, limit);

	return json(matches);
};
