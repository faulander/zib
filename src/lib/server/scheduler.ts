import cron, { type ScheduledTask } from 'node-cron';
import { refreshScheduledFeeds } from './feed-fetcher';
import { deleteOldArticles } from './articles';

let refreshTask: ScheduledTask | null = null;
let cleanupTask: ScheduledTask | null = null;

export function startScheduler() {
  // Refresh feeds every 15 minutes
  if (!refreshTask) {
    refreshTask = cron.schedule('*/15 * * * *', async () => {
      console.log('[Scheduler] Starting scheduled feed refresh...');
      try {
        // Refresh up to 100 feeds that need updating (based on TTL)
        const result = await refreshScheduledFeeds(100);
        console.log(`[Scheduler] Feed refresh complete. Added ${result.total_added} new articles.`);
      } catch (err) {
        console.error('[Scheduler] Feed refresh failed:', err);
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

  console.log('[Scheduler] Stopped');
}

// Initial refresh on startup (delayed to let the app start)
export async function initialRefresh() {
  console.log('[Scheduler] Running initial feed refresh...');
  try {
    // On startup, refresh feeds that need updating (based on TTL)
    const result = await refreshScheduledFeeds(100);
    console.log(`[Scheduler] Initial refresh complete. Added ${result.total_added} new articles.`);
  } catch (err) {
    console.error('[Scheduler] Initial refresh failed:', err);
  }
}
