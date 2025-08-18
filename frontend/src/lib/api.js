/**
 * API client for Zib RSS Reader backend
 */

const API_BASE_URL = 'http://localhost:8000';

class ApiError extends Error {
  constructor(message, status, response) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.response = response;
  }
}

class ApiClient {
  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorData.detail || errorMessage;
        } catch {
          // Use default error message if parsing fails
        }
        throw new ApiError(errorMessage, response.status, response);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        return data;
      }
      
      return await response.text();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Network error or other fetch errors
      throw new ApiError(
        `Network error: ${error.message}`, 
        0, 
        null
      );
    }
  }

  // Health check
  async getHealth() {
    return this.request('/health');
  }

  // Feeds endpoints
  async getFeeds() {
    return this.request('/api/feeds');
  }

  async getFeed(feedId) {
    return this.request(`/api/feeds/${feedId}`);
  }

  async createFeed(feedData) {
    return this.request('/api/feeds', {
      method: 'POST',
      body: JSON.stringify(feedData)
    });
  }

  async updateFeed(feedId, feedData) {
    return this.request(`/api/feeds/${feedId}`, {
      method: 'PUT',
      body: JSON.stringify(feedData)
    });
  }

  async deleteFeed(feedId) {
    return this.request(`/api/feeds/${feedId}`, {
      method: 'DELETE'
    });
  }

  async refreshFeed(feedId) {
    return this.request(`/api/feeds/${feedId}/refresh`, {
      method: 'POST'
    });
  }

  // Categories endpoints
  async getCategories(params = {}) {
    // Use the trailing slash to avoid redirects
    const searchParams = new URLSearchParams(params);
    const queryString = searchParams.toString();
    const endpoint = queryString ? `/api/categories/?${queryString}` : '/api/categories/';
    return this.request(endpoint);
  }

  async createCategory(categoryData) {
    return this.request('/api/categories', {
      method: 'POST',
      body: JSON.stringify(categoryData)
    });
  }

  async updateCategory(categoryId, categoryData) {
    return this.request(`/api/categories/${categoryId}`, {
      method: 'PUT',
      body: JSON.stringify(categoryData)
    });
  }

  async deleteCategory(categoryId) {
    return this.request(`/api/categories/${categoryId}`, {
      method: 'DELETE'
    });
  }

  // Articles endpoints
  async getArticles(params = {}) {
    const searchParams = new URLSearchParams();
    
    // Add query parameters
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, value.toString());
      }
    });

    const queryString = searchParams.toString();
    const endpoint = queryString ? `/api/articles?${queryString}` : '/api/articles';
    
    return this.request(endpoint);
  }

  async getArticle(articleId) {
    return this.request(`/api/articles/${articleId}`);
  }

  async markArticleRead(articleId, isRead = true) {
    const endpoint = isRead ? 'mark-read' : 'mark-unread';
    return this.request(`/api/articles/${articleId}/${endpoint}`, {
      method: 'POST'
    });
  }

  async starArticle(articleId, isStarred = true) {
    const endpoint = isStarred ? 'star' : 'unstar';
    return this.request(`/api/articles/${articleId}/${endpoint}`, {
      method: 'POST'
    });
  }

  async markAllRead(params = {}) {
    return this.request('/api/articles/mark-all-read', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }

  async bulkMarkRead(articleIds) {
    return this.request('/api/articles/bulk/mark-read', {
      method: 'POST',
      body: JSON.stringify({ article_ids: articleIds })
    });
  }

  async markCategoryAsRead(categoryId) {
    return this.request(`/api/articles/bulk/mark-read-by-category/${categoryId}`, {
      method: 'POST'
    });
  }

  // OPML endpoints
  async importOpml(opmlFile, options = {}) {
    const formData = new FormData();
    formData.append('file', opmlFile);
    formData.append('duplicate_strategy', options.duplicate_strategy || 'skip');
    formData.append('validate_feeds', options.validate_feeds !== false);
    formData.append('merge_categories', options.merge_categories !== false);
    if (options.category_parent_id) {
      formData.append('category_parent_id', options.category_parent_id);
    }
    
    return this.request('/api/import/opml', {
      method: 'POST',
      headers: {}, // Remove Content-Type header for FormData
      body: formData
    });
  }

  async exportOpml() {
    return this.request('/api/opml/export');
  }

  async getImportStatus(jobId) {
    return this.request(`/api/import/jobs/${jobId}`);
  }

  async getImportJobs(status = null, limit = 50) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (status) params.append('status', status);
    return this.request(`/api/import/jobs?${params.toString()}`);
  }

  async cancelImportJob(jobId) {
    return this.request(`/api/import/jobs/${jobId}`, {
      method: 'DELETE'
    });
  }

  // Search
  async searchArticles(query, params = {}) {
    const searchParams = new URLSearchParams({
      search: query,
      ...params
    });
    
    return this.request(`/api/articles?${searchParams.toString()}`);
  }

  // Settings endpoints
  async getUserSettings() {
    return this.request('/api/settings');
  }

  async updateUserSettings(settingsData) {
    return this.request('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(settingsData)
    });
  }
}

// Filter API
export const filters = {
  // Get all filters
  async getAll(activeOnly = false) {
    const params = activeOnly ? '?active_only=true' : '';
    return api.request(`/api/filters${params}`);
  },

  // Get specific filter
  async getById(filterId) {
    return api.request(`/api/filters/${filterId}`);
  },

  // Create filter
  async create(filterData) {
    return api.request('/api/filters', {
      method: 'POST',
      body: JSON.stringify(filterData)
    });
  },

  // Update filter
  async update(filterId, filterData) {
    return api.request(`/api/filters/${filterId}`, {
      method: 'PUT',
      body: JSON.stringify(filterData)
    });
  },

  // Delete filter
  async delete(filterId) {
    return api.request(`/api/filters/${filterId}`, {
      method: 'DELETE'
    });
  },

  // Toggle filter active state
  async toggle(filterId) {
    return api.request(`/api/filters/${filterId}/toggle`, {
      method: 'POST'
    });
  }
};

// Export singleton instance
export const api = new ApiClient();

// Export error class for error handling
export { ApiError };

// Export convenience functions
export const feeds = {
  getAll: () => api.getFeeds(),
  get: (id) => api.getFeed(id),
  create: (data) => api.createFeed(data),
  update: (id, data) => api.updateFeed(id, data),
  delete: (id) => api.deleteFeed(id),
  refresh: (id) => api.refreshFeed(id)
};

export const categories = {
  getAll: (params) => api.getCategories(params),
  create: (data) => api.createCategory(data),
  update: (id, data) => api.updateCategory(id, data),
  delete: (id) => api.deleteCategory(id)
};

export const articles = {
  getAll: (params) => api.getArticles(params),
  get: (id) => api.getArticle(id),
  markRead: (id, isRead) => api.markArticleRead(id, isRead),
  star: (id, isStarred) => api.starArticle(id, isStarred),
  markAllRead: (params) => api.markAllRead(params),
  bulkMarkRead: (articleIds) => api.bulkMarkRead(articleIds),
  markCategoryAsRead: (categoryId) => api.markCategoryAsRead(categoryId),
  search: (query, params) => api.searchArticles(query, params)
};

export const opml = {
  import: (file, options) => api.importOpml(file, options),
  export: () => api.exportOpml(),
  getImportStatus: (jobId) => api.getImportStatus(jobId),
  getImportJobs: (status, limit) => api.getImportJobs(status, limit),
  cancelImportJob: (jobId) => api.cancelImportJob(jobId)
};

export const userSettings = {
  get: () => api.getUserSettings(),
  update: (data) => api.updateUserSettings(data)
};

export default api;