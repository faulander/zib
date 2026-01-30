import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import {
  getAllSettings,
  setSetting,
  isInstapaperConfigured,
  type AppSettings
} from '$lib/server/settings';

export const GET: RequestHandler = async () => {
  const settings = getAllSettings();
  return json({
    ...settings,
    instapaperEnabled: isInstapaperConfigured()
  });
};

export const PATCH: RequestHandler = async ({ request }) => {
  const updates = (await request.json()) as Partial<AppSettings>;

  if (updates.hideReadArticles !== undefined) {
    setSetting('hideReadArticles', updates.hideReadArticles);
  }

  if (updates.compactListView !== undefined) {
    setSetting('compactListView', updates.compactListView);
  }

  if (updates.autoMarkAsRead !== undefined) {
    setSetting('autoMarkAsRead', updates.autoMarkAsRead);
  }

  if (updates.highlightColorLight !== undefined) {
    setSetting('highlightColorLight', updates.highlightColorLight);
  }

  if (updates.highlightColorDark !== undefined) {
    setSetting('highlightColorDark', updates.highlightColorDark);
  }

  if (updates.instapaperUsername !== undefined) {
    setSetting('instapaperUsername', updates.instapaperUsername);
  }

  if (updates.instapaperPassword !== undefined) {
    setSetting('instapaperPassword', updates.instapaperPassword);
  }

  if (updates.similarityThreshold !== undefined) {
    setSetting('similarityThreshold', updates.similarityThreshold);
  }

  const settings = getAllSettings();
  return json({
    ...settings,
    instapaperEnabled: isInstapaperConfigured()
  });
};
