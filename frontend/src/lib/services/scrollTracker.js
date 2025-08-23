/**
 * Simple scroll tracking service for mark read on scroll functionality
 * Uses optimal defaults - no user configuration needed
 */

import { apiActions } from '../stores/api.js';

class ScrollTracker {
  constructor() {
    this.observers = new Map(); // Map of element -> observer
    this.pendingReadArticles = new Set(); // Articles waiting to be marked as read
    this.batchTimeout = null;
    this.isRefreshing = false; // Flag to prevent tracking during refresh
    
    // Optimal defaults - no user configuration needed
    this.BATCH_SIZE = 3; // Small batches for responsive UI
    this.SCROLL_DELAY = 800; // 800ms delay after leaving viewport
    this.BATCH_TIMEOUT = 3000; // 3 seconds to process incomplete batches
  }
  
  /**
   * Start tracking an article element for scroll behavior
   * @param {HTMLElement} element - The article element to track
   * @param {Object} article - The article data
   */
  trackArticle(element, article) {
    if (!element || !article || this.isRefreshing) {
      return;
    }
    
    // Don't track articles that are already read
    if (article.read_status?.is_read) {
      return;
    }
    
    // Track visibility state for better scroll detection
    let hasBeenVisible = false;
    
    // Simple intersection observer - article leaves viewport = mark as read
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const rect = entry.boundingClientRect;
          if (entry.isIntersecting) {
            // Article is currently visible
            hasBeenVisible = true;
            // Mark as seen
            element.dataset.wasVisible = 'true';
          } else if (hasBeenVisible) {
            // Article was visible and now not intersecting - check where it went
            // Adaptive threshold based on viewport size and device type
            const isMobile = window.innerWidth < 768;
            const threshold = isMobile ? 170 : 170; // Adjusted based on actual layout behavior
            
            if (rect.bottom < threshold) {
              // Article has scrolled out of view - mark as read
              this.scheduleMarkAsRead(article.id);
              this.untrackArticle(element);
            }
          }
        });
      },
      {
        root: null, // Use viewport as root
        rootMargin: '0px',
        threshold: 0
      }
    );
    
    observer.observe(element);
    this.observers.set(element, observer);
  }
  
  /**
   * Stop tracking an article element
   * @param {HTMLElement} element - The article element to stop tracking
   */
  untrackArticle(element) {
    if (!element) return;
    
    const observer = this.observers.get(element);
    if (observer) {
      observer.disconnect();
      this.observers.delete(element);
    }
  }
  
  /**
   * Schedule an article to be marked as read after a delay
   * @param {number} articleId - The article ID
   */
  scheduleMarkAsRead(articleId) {
    // Add to pending batch after delay
    setTimeout(() => {
      this.addToBatch(articleId);
    }, this.SCROLL_DELAY);
  }
  
  /**
   * Add an article to the batch for marking as read
   * @param {number} articleId - The article ID
   */
  addToBatch(articleId) {
    this.pendingReadArticles.add(articleId);
    
    // Process immediately if batch is full
    if (this.pendingReadArticles.size >= this.BATCH_SIZE) {
      this.processBatch();
    } else {
      // Schedule processing if not already scheduled
      if (!this.batchTimeout) {
        this.batchTimeout = setTimeout(() => {
          this.processBatch();
        }, this.BATCH_TIMEOUT);
      }
    }
  }
  
  /**
   * Process the current batch of articles
   */
  async processBatch() {
    if (this.pendingReadArticles.size === 0) return;
    
    // Clear timeout
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
      this.batchTimeout = null;
    }
    
    // Get current batch
    const articleIds = Array.from(this.pendingReadArticles);
    this.pendingReadArticles.clear();
    
    try {
      // Mark articles as read
      for (const articleId of articleIds) {
        await apiActions.markArticleRead(articleId, true);
      }
    } catch (error) {
      console.error('[ScrollTracker] Failed to mark articles as read:', error);
    }
  }
  
  /**
   * Clean up all observers and pending operations
   */
  cleanup() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
    
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
      this.batchTimeout = null;
    }
    
    this.pendingReadArticles.clear();
  }
  
  /**
   * Force process any pending batch
   */
  forceProcessBatch() {
    if (this.pendingReadArticles.size > 0) {
      this.processBatch();
    }
  }
  
  /**
   * Pause tracking during refresh operations
   */
  pauseForRefresh() {
    this.isRefreshing = true;
  }
  
  /**
   * Resume tracking after refresh operations
   */
  resumeAfterRefresh() {
    this.isRefreshing = false;
    
    // Process any pending articles
    if (this.pendingReadArticles.size > 0 && !this.batchTimeout) {
      this.batchTimeout = setTimeout(() => {
        this.processBatch();
      }, this.BATCH_TIMEOUT);
    }
  }
}

// Create singleton instance
export const scrollTracker = new ScrollTracker();

// Make it accessible globally for debugging
if (typeof window !== 'undefined') {
  window.scrollTracker = scrollTracker;
}