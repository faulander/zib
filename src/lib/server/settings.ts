import { getDb } from './db';

export interface AppSettings {
  hideReadArticles: boolean;
  compactListView: boolean;
}

const DEFAULTS: AppSettings = {
  hideReadArticles: false,
  compactListView: false
};

export function getSetting<K extends keyof AppSettings>(key: K): AppSettings[K] {
  const db = getDb();
  const row = db.prepare('SELECT value FROM settings WHERE key = ?').get(key) as
    | { value: string }
    | undefined;

  if (!row) {
    return DEFAULTS[key];
  }

  // Parse based on type
  const defaultValue = DEFAULTS[key];
  if (typeof defaultValue === 'boolean') {
    return (row.value === 'true') as AppSettings[K];
  }

  return row.value as AppSettings[K];
}

export function setSetting<K extends keyof AppSettings>(key: K, value: AppSettings[K]): void {
  const db = getDb();
  db.prepare(
    'INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value'
  ).run(key, String(value));
}

export function getAllSettings(): AppSettings {
  return {
    hideReadArticles: getSetting('hideReadArticles'),
    compactListView: getSetting('compactListView')
  };
}
