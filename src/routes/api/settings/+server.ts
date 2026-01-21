import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllSettings, setSetting, type AppSettings } from '$lib/server/settings';

export const GET: RequestHandler = async () => {
  const settings = getAllSettings();
  return json(settings);
};

export const PATCH: RequestHandler = async ({ request }) => {
  const updates = (await request.json()) as Partial<AppSettings>;

  if (updates.hideReadArticles !== undefined) {
    setSetting('hideReadArticles', updates.hideReadArticles);
  }

  if (updates.compactListView !== undefined) {
    setSetting('compactListView', updates.compactListView);
  }

  if (updates.highlightColorLight !== undefined) {
    setSetting('highlightColorLight', updates.highlightColorLight);
  }

  if (updates.highlightColorDark !== undefined) {
    setSetting('highlightColorDark', updates.highlightColorDark);
  }

  const settings = getAllSettings();
  return json(settings);
};
