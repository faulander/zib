import { getDb } from './db';

export interface AppSettings {
  hideReadArticles: boolean;
  compactListView: boolean;
  autoMarkAsRead: boolean;
  highlightColorLight: string;
  highlightColorDark: string;
  // Instapaper integration
  instapaperUsername: string;
  instapaperPassword: string;
  // Similar articles grouping
  similarityThreshold: number;
  // Font size offset for list view (-2 to +2)
  fontSizeOffset: number;
}

const DEFAULTS: AppSettings = {
  hideReadArticles: false,
  compactListView: false,
  autoMarkAsRead: false,
  highlightColorLight: '#fef3c7', // amber-100
  highlightColorDark: '#422006', // amber-950
  instapaperUsername: '',
  instapaperPassword: '',
  similarityThreshold: 0.65,
  fontSizeOffset: 0
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
  if (typeof defaultValue === 'number') {
    return parseFloat(row.value) as AppSettings[K];
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
    compactListView: getSetting('compactListView'),
    autoMarkAsRead: getSetting('autoMarkAsRead'),
    highlightColorLight: getSetting('highlightColorLight'),
    highlightColorDark: getSetting('highlightColorDark'),
    instapaperUsername: getSetting('instapaperUsername'),
    instapaperPassword: getSetting('instapaperPassword'),
    similarityThreshold: getSetting('similarityThreshold'),
    fontSizeOffset: getSetting('fontSizeOffset')
  };
}

/**
 * Check if Instapaper is configured
 */
export function isInstapaperConfigured(): boolean {
  const username = getSetting('instapaperUsername');
  return username !== '';
}
