/**
 * Auto-refresh service for frontend article updates
 */

import { userSettings, articles } from '$lib/api.js';
import { feedsStore, categoriesStore, apiActions } from '$lib/stores/api.js';

class AutoRefreshService {
  constructor() {
    this.refreshTimer = null;
    this.isEnabled = false;
    this.intervalMinutes = 30;
    this.lastRefreshTime = null;
  }

  async start() {
    // Load user settings to check if auto-refresh is enabled
    try {
      const settings = await userSettings.get();
      this.isEnabled = settings.auto_refresh_feeds;
      this.intervalMinutes = settings.auto_refresh_interval_minutes;

      if (this.isEnabled) {
        this._startRefreshTimer();
        console.log(`Auto-refresh started: ${this.intervalMinutes} minute intervals`);
      }
    } catch (err) {
      console.error('Failed to start auto-refresh service:', err);
    }
  }

  stop() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
      console.log('Auto-refresh stopped');
    }
    this.isEnabled = false;
  }

  async updateSettings(settings) {
    this.isEnabled = settings.auto_refresh_feeds;
    this.intervalMinutes = settings.auto_refresh_interval_minutes;

    // Restart timer with new interval
    this.stop();
    if (this.isEnabled) {
      this._startRefreshTimer();
      console.log(`Auto-refresh updated: ${this.intervalMinutes} minute intervals`);
    }
  }

  _startRefreshTimer() {
    // Frontend refreshes 1 minute after backend refresh
    // Backend refreshes every N minutes, frontend checks N+1 minutes
    const frontendIntervalMs = (this.intervalMinutes + 1) * 60 * 1000;

    this.refreshTimer = setInterval(async () => {
      await this._refreshArticles();
    }, frontendIntervalMs);

    // Also do an initial refresh after 1 minute
    setTimeout(async () => {
      await this._refreshArticles();
    }, 60 * 1000);
  }

  async _refreshArticles() {
    try {
      console.log('Auto-refreshing frontend articles...');
      
      // Refresh feeds and categories data
      await apiActions.loadFeeds();
      await apiActions.loadCategories();
      
      // Reload unread counts to update sidebar numbers
      await apiActions.loadUnreadCounts();
      
      // Refresh articles in the current view
      await apiActions.loadArticles();
      
      this.lastRefreshTime = new Date();
      
      console.log('Frontend auto-refresh completed');
    } catch (err) {
      console.error('Auto-refresh failed:', err);
    }
  }

  getLastRefreshTime() {
    return this.lastRefreshTime;
  }
}

// Export singleton instance
export const autoRefreshService = new AutoRefreshService();