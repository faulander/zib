import { getDb } from './db';
import { mkdirSync, existsSync, readdirSync, unlinkSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';

const DB_PATH = process.env.DATABASE_PATH || 'data/rss.db';
const BACKUP_DIR = join(dirname(DB_PATH), 'backups');

export function createBackup(): string {
	mkdirSync(BACKUP_DIR, { recursive: true });

	const timestamp = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_').slice(0, 19);
	const backupPath = join(BACKUP_DIR, `rss_backup_${timestamp}.db`);

	const db = getDb();
	db.run(`VACUUM INTO '${backupPath.replace(/'/g, "''")}'`);

	return backupPath;
}

export function getBackupList(): { name: string; size: number; created_at: string }[] {
	if (!existsSync(BACKUP_DIR)) return [];

	return readdirSync(BACKUP_DIR)
		.filter((f) => f.endsWith('.db'))
		.map((name) => {
			const fullPath = join(BACKUP_DIR, name);
			const stat = statSync(fullPath);
			return {
				name,
				size: stat.size,
				created_at: stat.mtime.toISOString()
			};
		})
		.sort((a, b) => b.created_at.localeCompare(a.created_at));
}

export function cleanOldBackups(keepCount: number = 5): number {
	const backups = getBackupList();
	let deleted = 0;

	for (let i = keepCount; i < backups.length; i++) {
		try {
			unlinkSync(join(BACKUP_DIR, backups[i].name));
			deleted++;
		} catch {
			// Ignore deletion errors
		}
	}

	return deleted;
}
