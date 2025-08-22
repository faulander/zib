/**
 * Service for polling backend refresh status
 */

import { writable, get } from 'svelte/store';
import { feeds } from '../api.js';

// Store for refresh status
export const refreshStatus = writable({
  is_refreshing: false,
  last_refresh_started: null,
  last_refresh_completed: null,
  next_refresh_at: null,
  interval_minutes: 0,
  seconds_until_refresh: null,
  auto_refresh_enabled: false
});

// Store for last fetch time
export const lastStatusFetch = writable(null);

class RefreshStatusService {
  constructor() {
    this.pollInterval = null;
    this.pollIntervalMs = 10000; // 10 seconds
    this.lastCompletedRefresh = null;
  }

  /**
   * Start polling for refresh status
   */
  async start() {
    if (this.pollInterval) {
      // Refresh status service already running
      return; // Already running
    }

    // console.log('Starting refresh status service...');

    // Do initial fetch with error handling
    try {
      await this.fetchStatus();
    } catch (error) {
      console.error('Initial refresh status fetch failed:', error);
    }

    // Start polling
    this.pollInterval = setInterval(() => {
      this.fetchStatus().catch(error => {
        console.error('Polling refresh status failed:', error);
      });
    }, this.pollIntervalMs);
    
    // console.log(`Refresh status service started, polling every ${this.pollIntervalMs}ms`);
  }

  /**
   * Stop polling
   */
  stop() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  /**
   * Fetch refresh status from backend
   */
  async fetchStatus() {
    try {
      const status = await feeds.getRefreshStatus();
      
      // Check if a refresh just completed
      const currentStatus = get(refreshStatus);
      if (status.last_refresh_completed && 
          status.last_refresh_completed !== this.lastCompletedRefresh) {
        // A refresh just completed!
        this.lastCompletedRefresh = status.last_refresh_completed;
        
        // Trigger data refresh if we weren't already refreshing
        if (!currentStatus.is_refreshing) {
          this.onRefreshCompleted();
        }
      }

      // Update the store with explicit reactivity trigger
      refreshStatus.set({...status}); // Force new object to trigger reactivity
      lastStatusFetch.set(new Date());
      
    } catch (error) {
      console.error('Failed to fetch refresh status:', error);
    }
  }

  /**
   * Called when a refresh is completed on the backend
   */
  onRefreshCompleted() {
    // Backend refresh completed, trigger frontend data reload
    
    // Dispatch a custom event that components can listen to
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('backend-refresh-completed'));
    }
  }

  /**
   * Format time until next refresh (instance method)
   */
  formatTimeUntilRefresh(seconds) {
    if (!seconds || seconds < 0) return 'Now';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes === 0) {
      return `${remainingSeconds}s`;
    } else if (minutes < 60) {
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return `${hours}h ${remainingMinutes}m`;
    }
  }
}

// Create singleton instance
export const refreshStatusService = new RefreshStatusService();

// Auto-start on import in browser (with error handling)
if (typeof window !== 'undefined') {
  // Delay start to avoid blocking app initialization
  setTimeout(() => {
    refreshStatusService.start().catch(err => {
      console.error('Failed to start refresh status service:', err);
    });
  }, 3000); // Start after 3 seconds to ensure app is fully loaded
}