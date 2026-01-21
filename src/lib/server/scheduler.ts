import cron, { type ScheduledTask } from 'node-cron';
import { refreshScheduledFeeds } from './feed-fetcher';
import { deleteOldArticles } from './articles';
import { serverEvents, EVENTS } from './events';
import { recalculateAllFeedTTLs } from './adaptive-ttl';
import { logger, deleteOldLogs } from './logger';

let refreshTask: ScheduledTask | null = null;
let cleanupTask: ScheduledTask | null = null;
let ttlRecalcTask: ScheduledTask | null = null;
let isRefreshing = false;

export function startScheduler() {
  // Refresh feeds every 15 minutes
  if (!refreshTask) {
    refreshTask = cron.schedule('*/15 * * * *', async () => {
      if (isRefreshing) {
        logger.info('scheduler', 'Refresh already in progress, skipping');
        return;
      }

      isRefreshing = true;
      logger.info('scheduler', 'Starting scheduled feed refresh');
      try {
        // Refresh all feeds that need updating (no limit)
        const result = await refreshScheduledFeeds();
        logger.info('scheduler', `Feed refresh complete`, {
          added: result.total_added,
          feeds: Object.keys(result.feed_results).length
        });

        // Notify connected clients if new articles were added
        if (result.total_added > 0) {
          serverEvents.emit(EVENTS.FEEDS_REFRESHED, { added: result.total_added });
        }
      } catch (err) {
        logger.error('scheduler', 'Feed refresh failed', {
          error: err instanceof Error ? err.message : String(err)
        });
      } finally {
        isRefreshing = false;
      }
    });

    logger.info('scheduler', 'Feed refresh scheduled (every 15 minutes)');
  }

  // Clean up old read articles daily at 3am
  if (!cleanupTask) {
    cleanupTask = cron.schedule('0 3 * * *', async () => {
      logger.info('scheduler', 'Starting article cleanup');
      try {
        const deleted = deleteOldArticles(30); // Keep 30 days
        logger.info('scheduler', `Article cleanup complete`, { deleted });

        // Also clean up old logs (keep 7 days)
        const logsDeleted = deleteOldLogs(7);
        if (logsDeleted > 0) {
          logger.info('scheduler', `Log cleanup complete`, { deleted: logsDeleted });
        }
      } catch (err) {
        logger.error('scheduler', 'Article cleanup failed', {
          error: err instanceof Error ? err.message : String(err)
        });
      }
    });

    logger.info('scheduler', 'Article cleanup scheduled (daily at 3am)');
  }

  // Recalculate adaptive TTL values daily at 4am
  if (!ttlRecalcTask) {
    ttlRecalcTask = cron.schedule('0 4 * * *', async () => {
      logger.info('ttl', 'Starting TTL recalculation');
      try {
        const result = await recalculateAllFeedTTLs();
        logger.info('ttl', `TTL recalculation complete`, { updated: result.updated });
      } catch (err) {
        logger.error('ttl', 'TTL recalculation failed', {
          error: err instanceof Error ? err.message : String(err)
        });
      }
    });

    logger.info('scheduler', 'TTL recalculation scheduled (daily at 4am)');
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

  logger.info('scheduler', 'Scheduler stopped');
}

// Initial refresh on startup (delayed to let the app start)
export async function initialRefresh() {
  if (isRefreshing) {
    logger.info('scheduler', 'Refresh already in progress, skipping initial refresh');
    return;
  }

  // First, calculate TTL for any feeds missing statistics
  logger.info('ttl', 'Calculating initial TTL values');
  try {
    const ttlResult = await recalculateAllFeedTTLs();
    logger.info('ttl', `Initial TTL calculation complete`, { updated: ttlResult.updated });
  } catch (err) {
    logger.error('ttl', 'Initial TTL calculation failed', {
      error: err instanceof Error ? err.message : String(err)
    });
  }

  isRefreshing = true;
  logger.info('scheduler', 'Running initial feed refresh');
  try {
    // On startup, refresh feeds that need updating (no limit)
    const result = await refreshScheduledFeeds();
    logger.info('scheduler', `Initial refresh complete`, { added: result.total_added });
  } catch (err) {
    logger.error('scheduler', 'Initial refresh failed', {
      error: err instanceof Error ? err.message : String(err)
    });
  } finally {
    isRefreshing = false;
  }
}
