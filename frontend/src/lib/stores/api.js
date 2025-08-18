/**
 * API data stores for the Zib RSS Reader
 */

import { writable, derived, get } from 'svelte/store';
import { api, feeds, categories, articles } from '../api.js';

const API_BASE = 'http://localhost:8000/api';

// Loading states
export const isLoading = writable(false);
export const isLoadingMore = writable(false);
export const error = writable(null);

// Data stores
export const feedsStore = writable([]);
export const categoriesStore = writable([]);
export const articlesStore = writable([]);
export const totalArticleCount = writable(0);
export const hasMoreArticles = writable(true);

// Current selections
export const selectedFeed = writable(null);
export const selectedCategory = writable(null);
export const selectedArticle = writable(null);

// Filters
export const searchQuery = writable('');
export const showUnreadOnly = writable(false);
export const selectedFilter = writable('all'); // 'all', 'unread', 'starred'

// Cursor pagination
export const articlesLimit = writable(50);
export const nextCursor = writable(null);

// Derived stores
export const filteredFeeds = derived(
  [feedsStore, selectedCategory],
  ([$feeds, $selectedCategory]) => {
    if (!Array.isArray($feeds)) return [];
    if (!$selectedCategory) return $feeds;
    return $feeds.filter(feed => feed.category_id === $selectedCategory.id);
  }
);

// Store for unread counts - will be populated by API calls
export const unreadCounts = writable({ feeds: {}, categories: {} });

// API Actions
export const apiActions = {
  // Feeds
  async loadFeeds() {
    try {
      isLoading.set(true);
      error.set(null);
      const data = await feeds.getAll();
      // Backend now returns arrays directly (no pagination)
      if (Array.isArray(data)) {
        feedsStore.set(data);
      } else {
        feedsStore.set([]);
      }
      return data;
    } catch (err) {
      error.set(`Failed to load feeds: ${err.message}`);
      console.error('Failed to load feeds:', err);
      throw err;
    } finally {
      isLoading.set(false);
    }
  },

  async addFeed(feedData) {
    try {
      isLoading.set(true);
      error.set(null);
      const newFeed = await feeds.create(feedData);
      feedsStore.update(current => [...current, newFeed]);
      return newFeed;
    } catch (err) {
      error.set(`Failed to add feed: ${err.message}`);
      throw err;
    } finally {
      isLoading.set(false);
    }
  },

  async refreshFeed(feedId) {
    try {
      isLoading.set(true);
      error.set(null);
      const response = await fetch(`${API_BASE}/feeds/${feedId}/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // Reload feeds and articles to get updated counts
      await apiActions.loadFeeds();
      await apiActions.loadArticles();
      
      return result;
    } catch (err) {
      error.set(`Failed to refresh feed: ${err.message}`);
      throw err;
    } finally {
      isLoading.set(false);
    }
  },

  async refreshAllFeeds() {
    try {
      isLoading.set(true);
      error.set(null);
      const response = await fetch(`${API_BASE}/feeds/refresh-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // Reload feeds and articles to get updated counts
      await apiActions.loadFeeds();
      await apiActions.loadArticles();
      
      return result;
    } catch (err) {
      error.set(`Failed to refresh all feeds: ${err.message}`);
      throw err;
    } finally {
      isLoading.set(false);
    }
  },

  async deleteFeed(feedId) {
    try {
      isLoading.set(true);
      error.set(null);
      await feeds.delete(feedId);
      feedsStore.update(current => current.filter(f => f.id !== feedId));
    } catch (err) {
      error.set(`Failed to delete feed: ${err.message}`);
      throw err;
    } finally {
      isLoading.set(false);
    }
  },

  // Categories
  async loadCategories() {
    try {
      isLoading.set(true);
      error.set(null);
      const data = await categories.getAll();
      // Backend now returns arrays directly (no pagination)
      if (Array.isArray(data)) {
        categoriesStore.set(data);
      } else {
        categoriesStore.set([]);
      }
      return data;
    } catch (err) {
      error.set(`Failed to load categories: ${err.message}`);
      console.error('Failed to load categories:', err);
      throw err;
    } finally {
      isLoading.set(false);
    }
  },

  async addCategory(categoryData) {
    try {
      isLoading.set(true);
      error.set(null);
      const newCategory = await categories.create(categoryData);
      categoriesStore.update(current => [...current, newCategory]);
      return newCategory;
    } catch (err) {
      error.set(`Failed to add category: ${err.message}`);
      throw err;
    } finally {
      isLoading.set(false);
    }
  },

  // Articles
  async loadArticles(params = {}) {
    try {
      isLoading.set(true);
      error.set(null);
      
      // Reset cursor when loading fresh articles
      nextCursor.set(null);
      
      // Build query parameters
      const queryParams = { ...params };
      
      // Add filters
      const currentFilter = get(selectedFilter);
      if (currentFilter !== 'all') {
        queryParams.read_status = currentFilter;
      }
      
      const currentFeed = get(selectedFeed);
      if (currentFeed) {
        queryParams.feed_id = currentFeed.id;
      }
      
      const currentCategory = get(selectedCategory);
      if (currentCategory) {
        queryParams.category_id = currentCategory.id;
      }
      
      const currentSearch = get(searchQuery);
      if (currentSearch) {
        queryParams.search = currentSearch;
      }
      
      // Add cursor pagination
      queryParams.limit = get(articlesLimit);
      
      // Explicitly set sorting parameters for newest articles first
      queryParams.sort = 'published_date';
      queryParams.order = 'desc';
      
      console.log('Loading articles with params:', queryParams);
      const data = await articles.getAll(queryParams);
      console.log('API response:', data);
      // Handle cursor-based response
      if (data.articles) {
        articlesStore.set(data.articles);
        totalArticleCount.set(data.pagination?.total || data.articles.length);
        hasMoreArticles.set(data.has_more || false);
        nextCursor.set(data.next_cursor);
      } else if (data.items) {
        articlesStore.set(data.items);
        totalArticleCount.set(data.total || data.items.length);
        hasMoreArticles.set(false);
        nextCursor.set(null);
      } else if (Array.isArray(data)) {
        articlesStore.set(data);
        totalArticleCount.set(data.length);
        hasMoreArticles.set(false);
        nextCursor.set(null);
      } else {
        articlesStore.set([]);
        totalArticleCount.set(0);
        hasMoreArticles.set(false);
        nextCursor.set(null);
      }
      return data;
    } catch (err) {
      error.set(`Failed to load articles: ${err.message}`);
      console.error('Failed to load articles:', err);
      throw err;
    } finally {
      isLoading.set(false);
    }
  },

  // Load more articles for infinite scrolling
  async loadMoreArticles() {
    try {
      // Don't load if already loading or no more articles
      if (get(isLoadingMore) || !get(hasMoreArticles)) {
        return;
      }
      
      const currentCursor = get(nextCursor);
      if (!currentCursor) {
        return; // No cursor available
      }
      
      isLoadingMore.set(true);
      error.set(null);
      
      // Build query parameters (same as loadArticles)
      const queryParams = {};
      
      // Add filters
      const currentFilter = get(selectedFilter);
      if (currentFilter !== 'all') {
        queryParams.read_status = currentFilter;
      }
      
      const currentFeed = get(selectedFeed);
      if (currentFeed) {
        queryParams.feed_id = currentFeed.id;
      }
      
      const currentCategory = get(selectedCategory);
      if (currentCategory) {
        queryParams.category_id = currentCategory.id;
      }
      
      const currentSearch = get(searchQuery);
      if (currentSearch) {
        queryParams.search = currentSearch;
      }
      
      // Add cursor pagination
      queryParams.limit = get(articlesLimit);
      queryParams.since_id = currentCursor;
      
      // Explicitly set sorting parameters for newest articles first
      queryParams.sort = 'published_date';
      queryParams.order = 'desc';
      
      const data = await articles.getAll(queryParams);
      
      // Append new articles to existing ones (with deduplication)
      if (data.articles && Array.isArray(data.articles)) {
        articlesStore.update(currentArticles => {
          // Get existing article IDs for deduplication
          const existingIds = new Set(currentArticles.map(a => a.id));
          
          // Filter out duplicates from new articles
          const newArticles = data.articles.filter(article => !existingIds.has(article.id));
          
          console.log(`[LoadMore] Appending ${newArticles.length} new articles (${data.articles.length - newArticles.length} duplicates filtered)`);
          
          return [...currentArticles, ...newArticles];
        });
        
        // Update cursor state
        hasMoreArticles.set(data.has_more || false);
        nextCursor.set(data.next_cursor);
      } else {
        hasMoreArticles.set(false);
        nextCursor.set(null);
      }
      
      return data;
    } catch (err) {
      error.set(`Failed to load more articles: ${err.message}`);
      console.error('Failed to load more articles:', err);
      throw err;
    } finally {
      isLoadingMore.set(false);
    }
  },

  async markArticleRead(articleId, isRead = true) {
    try {
      const currentFilter = get(selectedFilter);
      
      // Check if article should be removed from current view
      // Don't remove from unread filter to prevent UI jumping
      const shouldRemove = (currentFilter === 'starred' && isRead && !get(articlesStore).find(a => a.id === articleId)?.read_status?.is_starred);
      
      if (shouldRemove) {
        // Remove article from current view (only for starred filter)
        articlesStore.update(current => current.filter(article => article.id !== articleId));
      } else {
        // Update article state in current view (keep in place for unread filter)
        articlesStore.update(current => 
          current.map(article => 
            article.id === articleId 
              ? { 
                  ...article, 
                  read_status: { 
                    ...article.read_status, 
                    is_read: isRead,
                    read_at: isRead ? new Date().toISOString() : null
                  }
                }
              : article
          )
        );
      }
      
      // Then make API call
      await articles.markRead(articleId, isRead);
      
      // Update unread counts locally without API calls to preserve scroll position
      if (isRead) {
        // Find the article to get its feed and category info
        const article = get(articlesStore).find(a => a.id === articleId);
        if (article) {
          unreadCounts.update(counts => {
            const newCounts = { ...counts };
            
            // Decrease feed count
            if (article.feed?.id && newCounts.feeds[article.feed.id] > 0) {
              newCounts.feeds[article.feed.id]--;
            }
            
            // Decrease category count
            if (article.feed?.category?.id && newCounts.categories[article.feed.category.id] > 0) {
              newCounts.categories[article.feed.category.id]--;
            }
            
            return newCounts;
          });
        }
      } else {
        // Increase counts when marking as unread
        const article = get(articlesStore).find(a => a.id === articleId);
        if (article) {
          unreadCounts.update(counts => {
            const newCounts = { ...counts };
            
            // Increase feed count
            if (article.feed?.id) {
              newCounts.feeds[article.feed.id] = (newCounts.feeds[article.feed.id] || 0) + 1;
            }
            
            // Increase category count
            if (article.feed?.category?.id) {
              newCounts.categories[article.feed.category.id] = (newCounts.categories[article.feed.category.id] || 0) + 1;
            }
            
            return newCounts;
          });
        }
      }
    } catch (err) {
      // Revert local state on error
      const currentFilter = get(selectedFilter);
      const shouldRemove = (currentFilter === 'starred' && isRead && !get(articlesStore).find(a => a.id === articleId)?.read_status?.is_starred);
      
      if (shouldRemove) {
        // Re-add the article if it was removed
        // We need to reload the articles to get the proper data back
        await this.loadArticles();
      } else {
        // Revert the article state change
        articlesStore.update(current => 
          current.map(article => 
            article.id === articleId 
              ? { 
                  ...article, 
                  read_status: { 
                    ...article.read_status, 
                    is_read: !isRead,
                    read_at: !isRead ? new Date().toISOString() : null
                  }
                }
              : article
          )
        );
      }
      error.set(`Failed to mark article: ${err.message}`);
      throw err;
    }
  },

  async starArticle(articleId, isStarred = true) {
    try {
      const currentFilter = get(selectedFilter);
      
      // Check if article should be removed from starred view when unstarred
      const shouldRemove = (currentFilter === 'starred' && !isStarred);
      
      if (shouldRemove) {
        // Remove article from current view
        articlesStore.update(current => current.filter(article => article.id !== articleId));
      } else {
        // Update article state in current view
        articlesStore.update(current => 
          current.map(article => 
            article.id === articleId 
              ? { 
                  ...article, 
                  read_status: { 
                    ...article.read_status, 
                    is_starred: isStarred,
                    starred_at: isStarred ? new Date().toISOString() : null
                  }
                }
              : article
          )
        );
      }
      
      // Then make API call
      await articles.star(articleId, isStarred);
    } catch (err) {
      // Revert local state on error
      const currentFilter = get(selectedFilter);
      const shouldRemove = (currentFilter === 'starred' && !isStarred);
      
      if (shouldRemove) {
        // Re-add the article if it was removed
        // We need to reload the articles to get the proper data back
        await this.loadArticles();
      } else {
        // Revert the article state change
        articlesStore.update(current => 
          current.map(article => 
            article.id === articleId 
              ? { 
                  ...article, 
                  read_status: { 
                    ...article.read_status, 
                    is_starred: !isStarred,
                    starred_at: !isStarred ? new Date().toISOString() : null
                  }
                }
              : article
          )
        );
      }
      error.set(`Failed to star article: ${err.message}`);
      throw err;
    }
  },

  async markAllRead(params = {}) {
    try {
      isLoading.set(true);
      error.set(null);
      
      await articles.markAllRead(params);
      
      // Reload data
      await this.loadArticles();
      await this.loadFeeds();
    } catch (err) {
      error.set(`Failed to mark all read: ${err.message}`);
      throw err;
    } finally {
      isLoading.set(false);
    }
  },

  async markCategoryAsRead(categoryId) {
    try {
      error.set(null);
      
      // Mark all articles in the category as read using the specific endpoint
      await articles.markCategoryAsRead(categoryId);
      
      // Update local unread counts for this category
      unreadCounts.update(counts => {
        const newCounts = { ...counts };
        newCounts.categories[categoryId] = 0;
        
        // Also reset counts for all feeds in this category
        const currentFeeds = get(feedsStore);
        const categoryFeeds = currentFeeds.filter(feed => feed.category_id === categoryId);
        categoryFeeds.forEach(feed => {
          newCounts.feeds[feed.id] = 0;
        });
        
        return newCounts;
      });
      
      // If currently viewing this category, reload articles
      const currentCategory = get(selectedCategory);
      if (currentCategory && currentCategory.id === categoryId) {
        await this.loadArticles();
      }
    } catch (err) {
      error.set(`Failed to mark category as read: ${err.message}`);
      throw err;
    }
  },

  // Load unread counts for categories and feeds
  async loadUnreadCounts() {
    try {
      const counts = { feeds: {}, categories: {} };
      
      // Get current categories and feeds
      const categories = get(categoriesStore);
      const feeds = get(feedsStore);
      
      if (!Array.isArray(categories) || !Array.isArray(feeds)) {
        console.log('Categories or feeds not loaded yet, skipping count loading');
        return;
      }
      
      console.log(`Loading counts for ${categories.length} categories and ${feeds.length} feeds`);
      
      // For each category, get unread count
      const categoryPromises = categories.map(async (category) => {
        try {
          const response = await fetch(`${API_BASE}/articles?category_id=${category.id}&read_status=unread&limit=1`);
          if (response.ok) {
            const data = await response.json();
            const count = data.pagination?.total || 0;
            counts.categories[category.id] = count;
            console.log(`Category ${category.name} (${category.id}): ${count} unread articles`);
          } else {
            counts.categories[category.id] = 0;
          }
        } catch (err) {
          console.error(`Failed to get count for category ${category.id}:`, err);
          counts.categories[category.id] = 0;
        }
      });
      
      // For each feed, get unread count  
      const feedPromises = feeds.map(async (feed) => {
        try {
          const response = await fetch(`${API_BASE}/articles?feed_id=${feed.id}&read_status=unread&limit=1`);
          if (response.ok) {
            const data = await response.json();
            const count = data.pagination?.total || 0;
            counts.feeds[feed.id] = count;
          } else {
            counts.feeds[feed.id] = 0;
          }
        } catch (err) {
          console.error(`Failed to get count for feed ${feed.id}:`, err);
          counts.feeds[feed.id] = 0;
        }
      });
      
      // Wait for all requests to complete
      await Promise.all([...categoryPromises, ...feedPromises]);
      
      console.log('Final counts:', counts);
      unreadCounts.set(counts);
      return counts;
    } catch (err) {
      console.error('Failed to load unread counts:', err);
      throw err;
    }
  },

  // Health check
  async checkHealth() {
    try {
      const health = await api.getHealth();
      return health;
    } catch (err) {
      error.set(`Backend connection failed: ${err.message}`);
      throw err;
    }
  }
};

// Initialize data
export async function initializeApp() {
  try {
    await apiActions.checkHealth();
    
    // Load user settings first to get default view
    const { userSettings } = await import('../api.js');
    const settings = await userSettings.get();
    selectedFilter.set(settings.default_view);
    
    await Promise.all([
      apiActions.loadCategories(),
      apiActions.loadFeeds()
    ]);
    await apiActions.loadArticles();
    // Load unread counts after we have categories and feeds
    await apiActions.loadUnreadCounts();
  } catch (err) {
    console.error('Failed to initialize app:', err);
    // App will continue with empty/mock data
  }
}