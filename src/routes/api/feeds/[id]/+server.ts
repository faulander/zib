import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getFeedById, updateFeed, deleteFeed } from '$lib/server/feeds';
import { getFeedStatistics, setTTLOverride } from '$lib/server/feed-stats';
import { getEffectiveTTL, formatTTL } from '$lib/server/adaptive-ttl';
import type { UpdateFeed } from '$lib/types';

export const GET: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid feed ID' }, { status: 400 });
  }

  const feed = getFeedById(id);

  if (!feed) {
    return json({ error: 'Feed not found' }, { status: 404 });
  }

  // Include statistics if available
  const stats = getFeedStatistics(id);
  const effectiveTTL = getEffectiveTTL(id);

  return json({
    ...feed,
    statistics: stats
      ? {
          avg_articles_per_day: stats.avg_articles_per_day,
          articles_last_7_days: stats.articles_last_7_days,
          articles_last_30_days: stats.articles_last_30_days,
          read_rate: stats.read_rate,
          engagement_rate: stats.engagement_rate,
          calculated_ttl_minutes: stats.calculated_ttl_minutes,
          ttl_override_minutes: stats.ttl_override_minutes,
          ttl_calculation_reason: stats.ttl_calculation_reason,
          last_calculated_at: stats.last_calculated_at
        }
      : null,
    effective_ttl_minutes: effectiveTTL,
    effective_ttl_display: formatTTL(effectiveTTL)
  });
};

export const PUT: RequestHandler = async ({ params, request }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid feed ID' }, { status: 400 });
  }

  const data: UpdateFeed = await request.json();
  const feed = updateFeed(id, data);

  if (!feed) {
    return json({ error: 'Feed not found' }, { status: 404 });
  }

  return json(feed);
};

export const PATCH: RequestHandler = async ({ params, request }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid feed ID' }, { status: 400 });
  }

  const data: UpdateFeed & { ttl_override_minutes?: number | null } = await request.json();

  // Handle TTL override separately
  if ('ttl_override_minutes' in data) {
    setTTLOverride(id, data.ttl_override_minutes ?? null);
    delete data.ttl_override_minutes;
  }

  // Update feed if there are other fields
  if (Object.keys(data).length > 0) {
    const feed = updateFeed(id, data);
    if (!feed) {
      return json({ error: 'Feed not found' }, { status: 404 });
    }
  }

  // Return updated feed with statistics
  const feed = getFeedById(id);
  if (!feed) {
    return json({ error: 'Feed not found' }, { status: 404 });
  }

  const stats = getFeedStatistics(id);
  const effectiveTTL = getEffectiveTTL(id);

  return json({
    ...feed,
    statistics: stats
      ? {
          avg_articles_per_day: stats.avg_articles_per_day,
          articles_last_7_days: stats.articles_last_7_days,
          articles_last_30_days: stats.articles_last_30_days,
          read_rate: stats.read_rate,
          engagement_rate: stats.engagement_rate,
          calculated_ttl_minutes: stats.calculated_ttl_minutes,
          ttl_override_minutes: stats.ttl_override_minutes,
          ttl_calculation_reason: stats.ttl_calculation_reason,
          last_calculated_at: stats.last_calculated_at
        }
      : null,
    effective_ttl_minutes: effectiveTTL,
    effective_ttl_display: formatTTL(effectiveTTL)
  });
};

export const DELETE: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid feed ID' }, { status: 400 });
  }

  const deleted = deleteFeed(id);

  if (!deleted) {
    return json({ error: 'Feed not found' }, { status: 404 });
  }

  return json({ success: true });
};
