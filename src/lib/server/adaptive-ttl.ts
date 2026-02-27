import { getDb } from './db';
import { calculateFeedStatistics, saveFeedStatistics, getFeedStatistics } from './feed-stats';
import type { FeedStatistics } from '$lib/types';

// TTL bounds in minutes
export const TTL_BOUNDS = {
  MIN_MINUTES: 5,      // Never refresh more than every 5 minutes
  MAX_MINUTES: 1440,   // Never wait more than 24 hours (1440 minutes)
  DEFAULT_MINUTES: 30  // Default for new feeds with no data
};

interface FeedRow {
  id: number;
  error_count: number;
}

interface TTLResult {
  ttl: number;
  reason: string;
}

/**
 * Calculate the optimal TTL for a feed based on publication frequency,
 * user engagement, and feed reliability.
 */
export function calculateAdaptiveTTL(
  stats: Omit<FeedStatistics, 'calculated_ttl_minutes' | 'ttl_override_minutes' | 'ttl_calculation_reason'>,
  feed: FeedRow
): TTLResult {
  // Check if we have enough data
  if (stats.total_articles_fetched < 5) {
    return {
      ttl: TTL_BOUNDS.DEFAULT_MINUTES,
      reason: 'insufficient data (< 5 articles)'
    };
  }

  // Factor 1: Publication Frequency (50% weight)
  // Maps avg_articles_per_day to base TTL
  let frequencyTTL: number;
  let frequencyReason: string;

  if (stats.avg_articles_per_day >= 20) {
    // Very high frequency (major news sites): 5-15 min
    frequencyTTL = Math.max(5, Math.round(15 - stats.avg_articles_per_day * 0.3));
    frequencyReason = 'high-frequency';
  } else if (stats.avg_articles_per_day >= 5) {
    // Medium-high (active blogs, tech news): 15-60 min
    frequencyTTL = Math.round(60 - (stats.avg_articles_per_day - 5) * 3);
    frequencyReason = 'medium-frequency';
  } else if (stats.avg_articles_per_day >= 1) {
    // Medium (daily blogs): 60-180 min
    frequencyTTL = Math.round(180 - (stats.avg_articles_per_day - 1) * 30);
    frequencyReason = 'daily';
  } else if (stats.avg_articles_per_day >= 0.14) {
    // Low (weekly): 180-720 min (3-12 hours)
    frequencyTTL = Math.round(720 - (stats.avg_articles_per_day * 7 - 1) * 90);
    frequencyReason = 'weekly';
  } else {
    // Very low (monthly or less): 720-1440 min (12-24 hours)
    frequencyTTL = TTL_BOUNDS.MAX_MINUTES;
    frequencyReason = 'infrequent';
  }

  // Factor 2: User Engagement (30% weight)
  // Based on articles opened, saved, or sent to Instapaper (not scroll-based read marks)
  let engagementMultiplier: number;
  let engagementReason: string;

  if (stats.engagement_rate >= 0.20) {
    engagementMultiplier = 0.5;  // Halve TTL for highly-engaged feeds
    engagementReason = 'high-engagement';
  } else if (stats.engagement_rate >= 0.10) {
    engagementMultiplier = 0.75;
    engagementReason = 'moderate-engagement';
  } else if (stats.engagement_rate >= 0.03) {
    engagementMultiplier = 1.0;
    engagementReason = 'low-engagement';
  } else {
    engagementMultiplier = 1.5;  // 50% longer TTL for rarely-engaged feeds
    engagementReason = 'minimal-engagement';
  }

  // Factor 3: Feed Reliability (20% weight)
  // Error-prone feeds get longer TTL to avoid hammering
  let reliabilityMultiplier: number;
  let reliabilityReason: string;

  if (feed.error_count === 0) {
    reliabilityMultiplier = 1.0;
    reliabilityReason = 'reliable';
  } else if (feed.error_count <= 3) {
    reliabilityMultiplier = 1.5;
    reliabilityReason = 'some-errors';
  } else if (feed.error_count <= 10) {
    reliabilityMultiplier = 2.0;
    reliabilityReason = 'error-prone';
  } else {
    reliabilityMultiplier = 4.0;  // Heavily penalize consistently failing feeds
    reliabilityReason = 'unreliable';
  }

  // Combine factors with weights:
  // - 50% frequency (base TTL)
  // - 30% engagement adjustment
  // - 20% reliability adjustment
  const baseTTL = frequencyTTL;
  const adjustedTTL = baseTTL * (0.5 + 0.3 * engagementMultiplier + 0.2 * reliabilityMultiplier);

  // Apply bounds
  const finalTTL = Math.max(
    TTL_BOUNDS.MIN_MINUTES,
    Math.min(TTL_BOUNDS.MAX_MINUTES, Math.round(adjustedTTL))
  );

  const reason = `${frequencyReason}, ${engagementReason}, ${reliabilityReason}`;

  return { ttl: finalTTL, reason };
}

/**
 * Recalculate statistics and TTL for a single feed
 */
export function recalculateFeedTTL(feedId: number): FeedStatistics {
  const db = getDb();

  // Get feed info for error count
  const feed = db.prepare('SELECT id, error_count FROM feeds WHERE id = ?').get(feedId) as FeedRow | null;

  if (!feed) {
    throw new Error(`Feed ${feedId} not found`);
  }

  // Calculate fresh statistics
  const stats = calculateFeedStatistics(feedId);

  // Calculate adaptive TTL
  const { ttl, reason } = calculateAdaptiveTTL(stats, feed);

  // Get existing override if any
  const existingStats = getFeedStatistics(feedId);
  const ttlOverride = existingStats?.ttl_override_minutes ?? null;

  // Build full statistics object
  const fullStats: FeedStatistics = {
    ...stats,
    calculated_ttl_minutes: ttl,
    ttl_override_minutes: ttlOverride,
    ttl_calculation_reason: reason
  };

  // Save to database
  saveFeedStatistics(fullStats);

  return fullStats;
}

/**
 * Recalculate statistics and TTL for all feeds
 */
export async function recalculateAllFeedTTLs(): Promise<{ updated: number }> {
  const db = getDb();
  const feeds = db.prepare('SELECT id FROM feeds').all() as { id: number }[];

  let updated = 0;

  for (const feed of feeds) {
    try {
      recalculateFeedTTL(feed.id);
      updated++;
    } catch (err) {
      console.error(`[AdaptiveTTL] Failed to recalculate TTL for feed ${feed.id}:`, err);
    }
  }

  return { updated };
}

/**
 * Get the effective TTL for a feed (override > calculated > default)
 */
export function getEffectiveTTL(feedId: number): number {
  const stats = getFeedStatistics(feedId);

  if (stats?.ttl_override_minutes !== null && stats?.ttl_override_minutes !== undefined) {
    return stats.ttl_override_minutes;
  }

  if (stats?.calculated_ttl_minutes !== null && stats?.calculated_ttl_minutes !== undefined) {
    return stats.calculated_ttl_minutes;
  }

  return TTL_BOUNDS.DEFAULT_MINUTES;
}

/**
 * Format TTL for display
 */
export function formatTTL(minutes: number): string {
  if (minutes < 60) {
    return `${minutes} min`;
  } else if (minutes < 1440) {
    const hours = Math.round(minutes / 60 * 10) / 10;
    return `${hours} hr`;
  } else {
    const days = Math.round(minutes / 1440 * 10) / 10;
    return `${days} day`;
  }
}
