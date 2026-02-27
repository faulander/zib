import { getDb } from './db';
import type { FeedStatistics } from '$lib/types';

export interface FeedStatsRow {
  feed_id: number;
  avg_articles_per_day: number;
  articles_last_7_days: number;
  articles_last_30_days: number;
  avg_publish_gap_hours: number | null;
  total_articles_fetched: number;
  total_articles_read: number;
  total_articles_starred: number;
  total_articles_engaged: number;
  read_rate: number;
  engagement_rate: number;
  calculated_ttl_minutes: number | null;
  ttl_override_minutes: number | null;
  ttl_calculation_reason: string | null;
  last_calculated_at: string | null;
}

interface ArticleStats {
  total: number;
  last_7_days: number;
  last_30_days: number;
}

interface EngagementStats {
  total: number;
  read_count: number;
  starred_count: number;
  engaged_count: number;
}

interface GapRow {
  gap_hours: number | null;
}

/**
 * Calculate statistics for a single feed based on its articles
 */
export function calculateFeedStatistics(feedId: number): Omit<FeedStatistics, 'calculated_ttl_minutes' | 'ttl_override_minutes' | 'ttl_calculation_reason'> {
  const db = getDb();

  // Get publication frequency data
  const articleStats = db.prepare(`
    SELECT
      COUNT(*) as total,
      COUNT(CASE WHEN datetime(published_at) > datetime('now', '-7 days') THEN 1 END) as last_7_days,
      COUNT(CASE WHEN datetime(published_at) > datetime('now', '-30 days') THEN 1 END) as last_30_days
    FROM articles
    WHERE feed_id = ? AND published_at IS NOT NULL
  `).get(feedId) as ArticleStats;

  // Calculate average articles per day (using last 30 days as baseline)
  const avgPerDay = articleStats.last_30_days / 30;

  // Get engagement data
  const engagementStats = db.prepare(`
    SELECT
      COUNT(*) as total,
      SUM(CASE WHEN is_read = 1 THEN 1 ELSE 0 END) as read_count,
      SUM(CASE WHEN is_starred = 1 THEN 1 ELSE 0 END) as starred_count,
      SUM(CASE WHEN is_opened = 1 OR is_saved = 1 OR is_sent_to_instapaper = 1 THEN 1 ELSE 0 END) as engaged_count
    FROM articles
    WHERE feed_id = ?
  `).get(feedId) as EngagementStats;

  const readRate = engagementStats.total > 0
    ? engagementStats.read_count / engagementStats.total
    : 0;

  const engagementRate = engagementStats.total > 0
    ? engagementStats.engaged_count / engagementStats.total
    : 0;

  // Calculate average gap between articles (using window function)
  // Note: SQLite supports window functions since 3.25.0
  const gaps = db.prepare(`
    WITH ordered_articles AS (
      SELECT
        published_at,
        LAG(published_at) OVER (ORDER BY published_at) as prev_published_at
      FROM articles
      WHERE feed_id = ? AND published_at IS NOT NULL
      ORDER BY published_at DESC
      LIMIT 20
    )
    SELECT
      (julianday(published_at) - julianday(prev_published_at)) * 24 as gap_hours
    FROM ordered_articles
    WHERE prev_published_at IS NOT NULL
  `).all(feedId) as GapRow[];

  const validGaps = gaps.filter((g) => g.gap_hours !== null && g.gap_hours > 0);
  const avgGapHours = validGaps.length > 0
    ? validGaps.reduce((sum, g) => sum + (g.gap_hours || 0), 0) / validGaps.length
    : null;

  return {
    feed_id: feedId,
    avg_articles_per_day: avgPerDay,
    articles_last_7_days: articleStats.last_7_days,
    articles_last_30_days: articleStats.last_30_days,
    avg_publish_gap_hours: avgGapHours,
    total_articles_fetched: engagementStats.total,
    total_articles_read: engagementStats.read_count,
    total_articles_starred: engagementStats.starred_count,
    total_articles_engaged: engagementStats.engaged_count,
    read_rate: readRate,
    engagement_rate: engagementRate,
    last_calculated_at: new Date().toISOString()
  };
}

/**
 * Get stored statistics for a feed
 */
export function getFeedStatistics(feedId: number): FeedStatsRow | null {
  const db = getDb();
  return db.prepare('SELECT * FROM feed_statistics WHERE feed_id = ?').get(feedId) as FeedStatsRow | null;
}

/**
 * Save or update feed statistics
 */
export function saveFeedStatistics(stats: FeedStatistics): void {
  const db = getDb();

  db.prepare(`
    INSERT INTO feed_statistics (
      feed_id, avg_articles_per_day, articles_last_7_days, articles_last_30_days,
      avg_publish_gap_hours, total_articles_fetched, total_articles_read,
      total_articles_starred, total_articles_engaged, read_rate, engagement_rate,
      calculated_ttl_minutes, ttl_override_minutes, ttl_calculation_reason, last_calculated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(feed_id) DO UPDATE SET
      avg_articles_per_day = excluded.avg_articles_per_day,
      articles_last_7_days = excluded.articles_last_7_days,
      articles_last_30_days = excluded.articles_last_30_days,
      avg_publish_gap_hours = excluded.avg_publish_gap_hours,
      total_articles_fetched = excluded.total_articles_fetched,
      total_articles_read = excluded.total_articles_read,
      total_articles_starred = excluded.total_articles_starred,
      total_articles_engaged = excluded.total_articles_engaged,
      read_rate = excluded.read_rate,
      engagement_rate = excluded.engagement_rate,
      calculated_ttl_minutes = excluded.calculated_ttl_minutes,
      ttl_calculation_reason = excluded.ttl_calculation_reason,
      last_calculated_at = excluded.last_calculated_at
  `).run(
    stats.feed_id,
    stats.avg_articles_per_day,
    stats.articles_last_7_days,
    stats.articles_last_30_days,
    stats.avg_publish_gap_hours,
    stats.total_articles_fetched,
    stats.total_articles_read,
    stats.total_articles_starred,
    stats.total_articles_engaged,
    stats.read_rate,
    stats.engagement_rate,
    stats.calculated_ttl_minutes,
    stats.ttl_override_minutes,
    stats.ttl_calculation_reason,
    stats.last_calculated_at
  );
}

/**
 * Update the TTL override for a feed (user manual setting)
 */
export function setTTLOverride(feedId: number, ttlMinutes: number | null): void {
  const db = getDb();

  // Ensure a row exists first
  const exists = db.prepare('SELECT 1 FROM feed_statistics WHERE feed_id = ?').get(feedId);

  if (exists) {
    db.prepare('UPDATE feed_statistics SET ttl_override_minutes = ? WHERE feed_id = ?')
      .run(ttlMinutes, feedId);
  } else {
    // Create a basic row with just the override
    db.prepare(`
      INSERT INTO feed_statistics (feed_id, ttl_override_minutes, created_at)
      VALUES (?, ?, ?)
    `).run(feedId, ttlMinutes, new Date().toISOString());
  }
}

/**
 * Get statistics for all feeds
 */
export function getAllFeedStatistics(): FeedStatsRow[] {
  const db = getDb();
  return db.prepare('SELECT * FROM feed_statistics').all() as FeedStatsRow[];
}
