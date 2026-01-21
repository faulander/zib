import cron, { type ScheduledTask } from 'node-cron';
import { refreshScheduledFeeds } from './feed-fetcher';
import { deleteOldArticles } from './articles';
import { serverEvents, EVENTS } from './events';
import { recalculateAllFeedTTLs } from './adaptive-ttl';

let refreshTask: ScheduledTask | null = null;
let cleanupTask: ScheduledTask | null = null;
let ttlRecalcTask: ScheduledTask | null = null;
let isRefreshing = false;

export function startScheduler() {
  // Refresh feeds every 15 minutes
  if (!refreshTask) {
    refreshTask = cron.schedule('*/15 * * * *', async () => {
      if (isRefreshing) {
        console.log('[Scheduler] Refresh already in progress, skipping...');
        return;
      }

      isRefreshing = true;
      console.log('[Scheduler] Starting scheduled feed refresh...');
      try {
        // Refresh all feeds that need updating (no limit)
        const result = await refreshScheduledFeeds();
        console.log(`[Scheduler] Feed refresh complete. Added ${result.total_added} new articles.`);

        // Notify connected clients if new articles were added
        if (result.total_added > 0) {
          serverEvents.emit(EVENTS.FEEDS_REFRESHED, { added: result.total_added });
        }
      } catch (err) {
        console.error('[Scheduler] Feed refresh failed:', err);
      } finally {
        isRefreshing = false;
      }
    });

    console.log('[Scheduler] Feed refresh scheduled (every 15 minutes)');
  }

  // Clean up old read articles daily at 3am
  if (!cleanupTask) {
    cleanupTask = cron.schedule('0 3 * * *', async () => {
      console.log('[Scheduler] Starting article cleanup...');
      try {
        const deleted = deleteOldArticles(30); // Keep 30 days
        console.log(`[Scheduler] Cleanup complete. Deleted ${deleted} old articles.`);
      } catch (err) {
        console.error('[Scheduler] Article cleanup failed:', err);
      }
    });

    console.log('[Scheduler] Article cleanup scheduled (daily at 3am)');
  }

  // Recalculate adaptive TTL values daily at 4am
  if (!ttlRecalcTask) {
    ttlRecalcTask = cron.schedule('0 4 * * *', async () => {
      console.log('[Scheduler] Starting TTL recalculation...');
      try {
        const result = await recalculateAllFeedTTLs();
        console.log(`[Scheduler] TTL recalculation complete. Updated ${result.updated} feeds.`);
      } catch (err) {
        console.error('[Scheduler] TTL recalculation failed:', err);
      }
    });

    console.log('[Scheduler] TTL recalculation scheduled (daily at 4am)');
  }
}

export function stopScheduler() {
  if (refreshTask) {
    refreshTask.stop();
    refreshTask = null;
  }

  if (cleanupTask) {
    cleanupTask.stop();
    cleanupTask = null;
  }

  if (ttlRecalcTask) {
    ttlRecalcTask.stop();
    ttlRecalcTask = null;
  }

  console.log('[Scheduler] Stopped');
}

// Initial refresh on startup (delayed to let the app start)
export async function initialRefresh() {
  if (isRefreshing) {
    console.log('[Scheduler] Refresh already in progress, skipping initial refresh...');
    return;
  }

  // First, calculate TTL for any feeds missing statistics
  console.log('[Scheduler] Calculating initial TTL values...');
  try {
    const ttlResult = await recalculateAllFeedTTLs();
    console.log(
      `[Scheduler] Initial TTL calculation complete. Updated ${ttlResult.updated} feeds.`
    );
  } catch (err) {
    console.error('[Scheduler] Initial TTL calculation failed:', err);
  }

  isRefreshing = true;
  console.log('[Scheduler] Running initial feed refresh...');
  try {
    // On startup, refresh feeds that need updating (no limit)
    const result = await refreshScheduledFeeds();
    console.log(`[Scheduler] Initial refresh complete. Added ${result.total_added} new articles.`);
  } catch (err) {
    console.error('[Scheduler] Initial refresh failed:', err);
  } finally {
    isRefreshing = false;
  }
}
