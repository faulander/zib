import { getDb } from './db';
import type { FolderRow, Folder, CreateFolder, UpdateFolder } from '$lib/types';

export function getAllFolders(): Folder[] {
  const db = getDb();

  const folders = db
    .prepare(
      `
    SELECT f.*,
           COALESCE(SUM(CASE WHEN a.is_read = 0 THEN 1 ELSE 0 END), 0) as unread_count
    FROM folders f
    LEFT JOIN feeds fe ON fe.folder_id = f.id
    LEFT JOIN articles a ON a.feed_id = fe.id
    GROUP BY f.id
    ORDER BY f.position, f.name
  `
    )
    .all() as (FolderRow & { unread_count: number })[];

  return folders;
}

export function getFolderById(id: number): Folder | null {
  const db = getDb();

  const folder = db
    .prepare(
      `
    SELECT f.*,
           COALESCE(SUM(CASE WHEN a.is_read = 0 THEN 1 ELSE 0 END), 0) as unread_count
    FROM folders f
    LEFT JOIN feeds fe ON fe.folder_id = f.id
    LEFT JOIN articles a ON a.feed_id = fe.id
    WHERE f.id = ?
    GROUP BY f.id
  `
    )
    .get(id) as (FolderRow & { unread_count: number }) | undefined;

  return folder || null;
}

export function createFolder(data: CreateFolder): Folder {
  const db = getDb();

  const maxPosition = db
    .prepare('SELECT COALESCE(MAX(position), -1) + 1 as next_position FROM folders')
    .get() as { next_position: number };

  const position = data.position ?? maxPosition.next_position;

  const result = db
    .prepare('INSERT INTO folders (name, position) VALUES (?, ?)')
    .run(data.name, position);

  return getFolderById(result.lastInsertRowid as number)!;
}

export function updateFolder(id: number, data: UpdateFolder): Folder | null {
  const db = getDb();

  const existing = db.prepare('SELECT * FROM folders WHERE id = ?').get(id) as FolderRow | undefined;

  if (!existing) {
    return null;
  }

  const updates: string[] = [];
  const values: (string | number)[] = [];

  if (data.name !== undefined) {
    updates.push('name = ?');
    values.push(data.name);
  }

  if (data.position !== undefined) {
    updates.push('position = ?');
    values.push(data.position);
  }

  if (updates.length > 0) {
    values.push(id);
    db.prepare(`UPDATE folders SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  return getFolderById(id);
}

export function deleteFolder(id: number): boolean {
  const db = getDb();
  const result = db.prepare('DELETE FROM folders WHERE id = ?').run(id);
  return result.changes > 0;
}

export function reorderFolders(items: { id: number; position: number }[]): void {
  const db = getDb();
  const stmt = db.prepare('UPDATE folders SET position = ? WHERE id = ?');
  const tx = db.transaction(() => {
    for (const item of items) {
      stmt.run(item.position, item.id);
    }
  });
  tx();
}
