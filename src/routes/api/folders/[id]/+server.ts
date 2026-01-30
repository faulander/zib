import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getFolderById, updateFolder, deleteFolder } from '$lib/server/folders';
import { getDb } from '$lib/server/db';
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

export const PATCH: RequestHandler = async ({ params, request }) => {
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

export const DELETE: RequestHandler = async ({ params, url }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid folder ID' }, { status: 400 });
  }

  const db = getDb();

  // Check if folder has feeds
  const feedCount = db
    .prepare('SELECT COUNT(*) as count FROM feeds WHERE folder_id = ?')
    .get(id) as { count: number };

  if (feedCount.count > 0) {
    // Check for action parameter: 'delete' or 'move'
    const action = url.searchParams.get('action');
    const targetFolderId = url.searchParams.get('target_folder_id');

    if (!action) {
      // Return info about feeds that need to be handled
      return json(
        {
          error: 'Folder has feeds',
          feedCount: feedCount.count,
          requiresAction: true
        },
        { status: 409 }
      );
    }

    if (action === 'delete') {
      // Delete all feeds and their articles in this folder
      const feeds = db.prepare('SELECT id FROM feeds WHERE folder_id = ?').all(id) as {
        id: number;
      }[];
      for (const feed of feeds) {
        db.prepare('DELETE FROM articles WHERE feed_id = ?').run(feed.id);
      }
      db.prepare('DELETE FROM feeds WHERE folder_id = ?').run(id);
    } else if (action === 'move') {
      // Move feeds to another folder (null for uncategorized)
      const newFolderId = targetFolderId ? parseInt(targetFolderId) : null;
      db.prepare('UPDATE feeds SET folder_id = ? WHERE folder_id = ?').run(newFolderId, id);
    } else {
      return json({ error: 'Invalid action. Use "delete" or "move"' }, { status: 400 });
    }
  }

  const deleted = deleteFolder(id);

  if (!deleted) {
    return json({ error: 'Folder not found' }, { status: 404 });
  }

  return json({ success: true });
};
