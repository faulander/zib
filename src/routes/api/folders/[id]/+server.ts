import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getFolderById, updateFolder, deleteFolder } from '$lib/server/folders';
import type { UpdateFolder } from '$lib/types';

export const GET: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid folder ID' }, { status: 400 });
  }

  const folder = getFolderById(id);

  if (!folder) {
    return json({ error: 'Folder not found' }, { status: 404 });
  }

  return json(folder);
};

export const PUT: RequestHandler = async ({ params, request }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid folder ID' }, { status: 400 });
  }

  const data: UpdateFolder = await request.json();
  const folder = updateFolder(id, data);

  if (!folder) {
    return json({ error: 'Folder not found' }, { status: 404 });
  }

  return json(folder);
};

export const DELETE: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid folder ID' }, { status: 400 });
  }

  const deleted = deleteFolder(id);

  if (!deleted) {
    return json({ error: 'Folder not found' }, { status: 404 });
  }

  return json({ success: true });
};
