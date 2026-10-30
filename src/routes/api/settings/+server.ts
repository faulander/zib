import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import {
  getAllSettings,
  setSetting,
  isInstapaperConfigured,
  isEmbeddingConfigured,
  type AppSettings
} from '$lib/server/settings';
import { getEmbeddingStats } from '$lib/server/embedding-job';
import { isThemeId } from '$lib/themes';

export const GET: RequestHandler = async () => {
  const settings = getAllSettings();
  const embeddingStats = getEmbeddingStats();
  return json({
    ...settings,
    instapaperEnabled: isInstapaperConfigured(),
    embeddingEnabled: isEmbeddingConfigured(),
    embeddingStats
  });
};

export const PATCH: RequestHandler = async ({ request }) => {
  const updates = (await request.json()) as Partial<AppSettings>;

  // Validate before writing anything so a bad theme doesn't leave a partial update
  if (updates.theme !== undefined && !isThemeId(updates.theme)) {
    return json({ error: 'Unknown theme' }, { status: 400 });
  }

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

  if (updates.similarityThresholdEmbedding !== undefined) {
    setSetting('similarityThresholdEmbedding', updates.similarityThresholdEmbedding);
  }

  if (updates.fontSizeOffset !== undefined) {
    setSetting('fontSizeOffset', updates.fontSizeOffset);
  }

  if (updates.fontSizeOffsetMobile !== undefined) {
    setSetting('fontSizeOffsetMobile', updates.fontSizeOffsetMobile);
  }

  if (updates.skipAgeFilter !== undefined) {
    setSetting('skipAgeFilter', updates.skipAgeFilter);
  }

  if (updates.highlightMode !== undefined) {
    setSetting('highlightMode', updates.highlightMode);
  }

  if (updates.embeddingProvider !== undefined) {
    setSetting('embeddingProvider', updates.embeddingProvider);
  }

  if (updates.embeddingModel !== undefined) {
    setSetting('embeddingModel', updates.embeddingModel);
  }

  if (updates.embeddingApiUrl !== undefined) {
    setSetting('embeddingApiUrl', updates.embeddingApiUrl);
  }

  if (updates.embeddingApiKey !== undefined) {
    setSetting('embeddingApiKey', updates.embeddingApiKey);
  }

  if (updates.embeddingRateLimit !== undefined) {
    setSetting('embeddingRateLimit', updates.embeddingRateLimit);
  }

  if (updates.theme !== undefined) {
    setSetting('theme', updates.theme);
  }

  const settings = getAllSettings();
  const embeddingStats = getEmbeddingStats();
  return json({
    ...settings,
    instapaperEnabled: isInstapaperConfigured(),
    embeddingEnabled: isEmbeddingConfigured(),
    embeddingStats
  });
};
