import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { createBackup, getBackupList, cleanOldBackups } from '$lib/server/backup';
import { readFileSync } from 'node:fs';

// GET — list backups or download a specific one
export const GET: RequestHandler = async ({ url }) => {
	const download = url.searchParams.get('download');

	if (download === 'latest') {
		try {
			const backupPath = createBackup();
			const data = readFileSync(backupPath);
			cleanOldBackups(5);

			return new Response(data, {
				headers: {
					'Content-Type': 'application/x-sqlite3',
					'Content-Disposition': `attachment; filename="zib_backup_${new Date().toISOString().slice(0, 10)}.db"`,
					'Content-Length': String(data.length)
				}
			});
		} catch (err) {
			return json(
				{ error: 'Failed to create backup: ' + (err instanceof Error ? err.message : String(err)) },
				{ status: 500 }
			);
		}
	}

	// List backups
	const backups = getBackupList();
	return json({ backups });
};

// POST — create a backup
export const POST: RequestHandler = async () => {
	try {
		const backupPath = createBackup();
		cleanOldBackups(5);
		const backups = getBackupList();
		return json({ success: true, path: backupPath, backups });
	} catch (err) {
		return json(
			{ error: 'Backup failed: ' + (err instanceof Error ? err.message : String(err)) },
			{ status: 500 }
		);
	}
};
