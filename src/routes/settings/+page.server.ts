import type { PageServerLoad } from './$types';
import { getAllFilters } from '$lib/server/filters';
import { getAllSettings } from '$lib/server/settings';
import { getFeedsWithErrors, getAllFeeds } from '$lib/server/feeds';
import { getAllFeedStatistics } from '$lib/server/feed-stats';
import { getEffectiveTTL, formatTTL } from '$lib/server/adaptive-ttl';
import { getLogs, getLogCount } from '$lib/server/logger';

export const load: PageServerLoad = async () => {
  const filters = getAllFilters();
  const settings = getAllSettings();
  const errorFeeds = getFeedsWithErrors();
  const allFeeds = getAllFeeds();
  const allStats = getAllFeedStatistics();

  // Build a map of feed stats
  const statsMap = new Map(allStats.map((s) => [s.feed_id, s]));

  // Enrich feeds with TTL info
  const feedsWithTTL = allFeeds.map((feed) => {
    const stats = statsMap.get(feed.id);
    const effectiveTTL = getEffectiveTTL(feed.id);
    return {
      ...feed,
      effective_ttl_minutes: effectiveTTL,
      effective_ttl_display: formatTTL(effectiveTTL),
      statistics: stats
        ? {
            avg_articles_per_day: stats.avg_articles_per_day,
            read_rate: stats.read_rate,
            calculated_ttl_minutes: stats.calculated_ttl_minutes,
            ttl_override_minutes: stats.ttl_override_minutes,
            ttl_calculation_reason: stats.ttl_calculation_reason
          }
        : null
    };
  });

  // Get recent logs
  const logs = getLogs({ limit: 50 });
  const logCount = getLogCount();

  return {
    filters,
    settings,
    errorFeeds,
    allFeeds: feedsWithTTL,
    logs,
    logCount
  };
};
