import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllFolders, createFolder } from '$lib/server/folders';
import type { CreateFolder } from '$lib/types';

export const GET: RequestHandler = async () => {
  const folders = getAllFolders();
  return json(folders);
};

export const POST: RequestHandler = async ({ request }) => {
  const data: CreateFolder = await request.json();

  if (!data.name || typeof data.name !== 'string') {
    return json({ error: 'Name is required' }, { status: 400 });
  }

  const folder = createFolder(data);
  return json(folder, { status: 201 });
};
