/**
 * Scroll tracking service for mark read on scroll functionality
 */

import { get } from 'svelte/store';
import { settings } from '../stores/settings.js';
import { apiActions } from '../stores/api.js';
import { articles } from '../api.js';

class ScrollTracker {
  constructor() {
    this.observers = new Map(); // Map of element -> observer
    this.pendingReadArticles = new Set(); // Articles waiting to be marked as read
    this.timeouts = new Map(); // Map of articleId -> timeout
    this.batchTimeout = null;
    
    // Subscribe to settings changes for batch size and delay
    settings.subscribe((currentSettings) => {
      this.batchSize = currentSettings.markReadScrollBatchSize || 5;
      this.scrollDelay = currentSettings.markReadScrollDelay || 1000;
    });
  }
  
  /**
   * Start tracking an article element for scroll behavior
   * @param {HTMLElement} element - The article element to track
   * @param {Object} article - The article data
   */
  trackArticle(element, article) {
    if (!element || !article) {
      return;
    }
    
    // Don't track articles that are already read
    if (article.read_status?.is_read) {
      return;
    };
    
    // Find the scrollable container that contains this article
    let scrollableContainer = null;
    let parent = element.parentElement;
    while (parent) {
      const style = window.getComputedStyle(parent);
      if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
        scrollableContainer = parent;
        break;
      }
      parent = parent.parentElement;
    }
    
    // Track the article's visibility history
    const visibilityState = {
      hasEverBeenVisible: false,
      lastScrollPosition: null,
      initialCheck: true
    };
    
    // Create intersection observer for this element
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const rect = entry.boundingClientRect;
          const isIntersecting = entry.isIntersecting;
          
          // On initial check, determine if article is already above viewport
          if (visibilityState.initialCheck) {
            visibilityState.initialCheck = false;
            
            // If article is initially above viewport, it was already scrolled past
            if (rect.bottom < 0) {
              // Article is above the viewport on initial check - user already scrolled past it
              // Don't mark as read because we don't know if user actually saw it
              return;
            }
          }
          
          if (isIntersecting) {
            // Article is currently visible
            visibilityState.hasEverBeenVisible = true;
            visibilityState.lastScrollPosition = rect.top;
          } else if (visibilityState.hasEverBeenVisible) {
            // Article was visible but now isn't - check if it scrolled out
            // Get the container bounds for proper viewport calculation
            const containerRect = scrollableContainer ? scrollableContainer.getBoundingClientRect() : 
                                 { top: 0, bottom: window.innerHeight };
            const containerTop = containerRect.top;
            const containerBottom = containerRect.bottom;
            
            // Check if article has scrolled out of the container view
            const scrolledOutTop = rect.bottom < containerTop; // Article is above container
            const scrolledOutBottom = rect.top > containerBottom; // Article is below container
            
            // Alternative: Check if the article has moved significantly up from its last position
            const hasScrolledUp = visibilityState.lastScrollPosition !== null && 
                                  rect.top < (visibilityState.lastScrollPosition - 30); // Moved up by at least 30px
            
            if ((scrolledOutTop || hasScrolledUp) && visibilityState.lastScrollPosition !== null) {
              this.scheduleMarkAsRead(article.id);
              this.untrackArticle(element);
            } else if (scrolledOutBottom && visibilityState.lastScrollPosition !== null) {
              this.scheduleMarkAsRead(article.id);
              this.untrackArticle(element);
            }
          }
        });
      },
      {
        root: scrollableContainer, // Use the article container as root instead of viewport
        rootMargin: '0px', // No margin needed since we're using the correct container
        threshold: 0 // Trigger when any part enters/leaves the container
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
    // Clear any existing timeout for this article
    this.cancelMarkAsRead(articleId);
    
    // Schedule marking as read after delay
    const timeout = setTimeout(() => {
      this.addToBatch(articleId);
      this.timeouts.delete(articleId);
    }, this.scrollDelay);
    
    this.timeouts.set(articleId, timeout);
  }
  
  /**
   * Cancel marking an article as read (used for cleanup only)
   * @param {number} articleId - The article ID
   */
  cancelMarkAsRead(articleId) {
    const timeout = this.timeouts.get(articleId);
    if (timeout) {
      clearTimeout(timeout);
      this.timeouts.delete(articleId);
    }
    
    // Also remove from pending batch if it's there
    this.pendingReadArticles.delete(articleId);
  }
  
  /**
   * Add an article to the batch for marking as read
   * @param {number} articleId - The article ID
   */
  addToBatch(articleId) {
    this.pendingReadArticles.add(articleId);
    
    // If we've reached batch size, process immediately
    if (this.pendingReadArticles.size >= this.batchSize) {
      this.processBatch();
    } else {
      // Otherwise, schedule processing after a longer delay to allow more articles to accumulate
      this.scheduleBatchProcessing();
    }
  }
  
  /**
   * Schedule batch processing if not already scheduled
   */
  scheduleBatchProcessing() {
    if (this.batchTimeout) return;
    
    this.batchTimeout = setTimeout(() => {
      this.processBatch();
    }, 5000); // Process after 5 seconds of inactivity
  }
  
  /**
   * Process the current batch of articles
   */
  async processBatch() {
    if (this.pendingReadArticles.size === 0) return;
    
    // Clear the batch timeout
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
      this.batchTimeout = null;
    }
    
    // Get current batch
    const articleIds = Array.from(this.pendingReadArticles);
    this.pendingReadArticles.clear();
    
    try {
      // Mark articles as read in batch
      await this.markArticlesBatch(articleIds);
    } catch (error) {
      console.error('[ScrollTracker] Failed to mark articles as read:', error);
      
      // Re-add failed articles to batch for retry
      articleIds.forEach(id => this.pendingReadArticles.add(id));
      this.scheduleBatchProcessing();
    }
  }
  
  /**
   * Mark multiple articles as read in a batch
   * @param {number[]} articleIds - Array of article IDs to mark as read
   */
  async markArticlesBatch(articleIds) {
    if (articleIds.length === 0) return;
    
    try {
      // Use the API client which handles the correct URL
      const result = await articles.bulkMarkRead(articleIds);
      
      // Update local state for each successfully marked article
      articleIds.forEach(articleId => {
        // Use the existing markArticleRead action but skip the API call
        // by calling it with a flag to only update local state
        apiActions.markArticleRead(articleId, true).catch(err => {
          console.error(`Failed to update local state for article ${articleId}:`, err);
        });
      });
      
      // Update unread counts after batch marking
      await apiActions.loadUnreadCounts();
      
      return result;
    } catch (error) {
      console.error('Failed to bulk mark articles as read:', error);
      
      // Fallback to individual API calls
      const promises = articleIds.map(articleId => 
        apiActions.markArticleRead(articleId, true).catch(error => {
          console.error(`Failed to mark article ${articleId} as read:`, error);
          return null;
        })
      );
      
      await Promise.allSettled(promises);
    }
  }
  
  /**
   * Clean up all observers and pending operations
   */
  cleanup() {
    // Disconnect all observers
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
    
    // Clear all timeouts
    this.timeouts.forEach(timeout => clearTimeout(timeout));
    this.timeouts.clear();
    
    // Clear batch timeout
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
      this.batchTimeout = null;
    }
    
    // Clear pending articles
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
}

// Create singleton instance
export const scrollTracker = new ScrollTracker();

// Make it accessible globally for debugging
if (typeof window !== 'undefined') {
  window.scrollTracker = scrollTracker;
}