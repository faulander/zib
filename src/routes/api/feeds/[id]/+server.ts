import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getFeedById, updateFeed, deleteFeed } from '$lib/server/feeds';
import type { UpdateFeed } from '$lib/types';

export const GET: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid feed ID' }, { status: 400 });
  }

  const feed = getFeedById(id);

  if (!feed) {
    return json({ error: 'Feed not found' }, { status: 404 });
  }

  return json(feed);
};

export const PUT: RequestHandler = async ({ params, request }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid feed ID' }, { status: 400 });
  }

  const data: UpdateFeed = await request.json();
  const feed = updateFeed(id, data);

  if (!feed) {
    return json({ error: 'Feed not found' }, { status: 404 });
  }

  return json(feed);
};

export const PATCH: RequestHandler = async ({ params, request }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid feed ID' }, { status: 400 });
  }

  const data: UpdateFeed = await request.json();
  const feed = updateFeed(id, data);

  if (!feed) {
    return json({ error: 'Feed not found' }, { status: 404 });
  }

  return json(feed);
};

export const DELETE: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid feed ID' }, { status: 400 });
  }

  const deleted = deleteFeed(id);

  if (!deleted) {
    return json({ error: 'Feed not found' }, { status: 404 });
  }

  return json({ success: true });
};
