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
        return await response.json();
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
  async getCategories() {
    return this.request('/api/categories');
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
    return this.request(`/api/articles/${articleId}/read`, {
      method: 'PUT',
      body: JSON.stringify({ is_read: isRead })
    });
  }

  async starArticle(articleId, isStarred = true) {
    return this.request(`/api/articles/${articleId}/star`, {
      method: 'PUT',
      body: JSON.stringify({ is_starred: isStarred })
    });
  }

  async markAllRead(params = {}) {
    return this.request('/api/articles/mark-all-read', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }

  // OPML endpoints
  async importOpml(opmlFile) {
    const formData = new FormData();
    formData.append('file', opmlFile);
    
    return this.request('/api/opml/import', {
      method: 'POST',
      headers: {}, // Remove Content-Type header for FormData
      body: formData
    });
  }

  async exportOpml() {
    return this.request('/api/opml/export');
  }

  async getImportStatus(jobId) {
    return this.request(`/api/opml/import/${jobId}/status`);
  }

  // Search
  async searchArticles(query, params = {}) {
    const searchParams = new URLSearchParams({
      search: query,
      ...params
    });
    
    return this.request(`/api/articles?${searchParams.toString()}`);
  }
}

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
  getAll: () => api.getCategories(),
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
  search: (query, params) => api.searchArticles(query, params)
};

export default api;