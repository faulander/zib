# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-16-rss-reader-core/spec.md

> Created: 2025-08-16
> Version: 1.0.0

## Endpoints

### GET /api/articles

**Purpose:** Retrieve articles with filtering and pagination
**Parameters:** 
- `page` (int, optional): Page number (default: 1)
- `page_size` (int, optional): Items per page (default: 20, max: 100)
- `feed_id` (int, optional): Filter by specific feed
- `category_id` (int, optional): Filter by feed category
- `is_read` (bool, optional): Filter by read status
- `since` (datetime, optional): Articles published after this date
- `until` (datetime, optional): Articles published before this date
- `search` (string, optional): Search in title and content
**Response:** 
```json
{
  "items": [
    {
      "id": 123,
      "feed_id": 45,
      "url": "https://example.com/article",
      "guid": "unique-guid-123",
      "title": "Article Title",
      "summary": "Brief summary",
      "content": "Full article content",
      "author": "Author Name",
      "published_at": "2025-08-16T10:00:00Z",
      "updated_at": "2025-08-16T10:05:00Z",
      "is_read": false,
      "read_at": null,
      "created_at": "2025-08-16T10:10:00Z",
      "feed": {
        "id": 45,
        "title": "Feed Title",
        "url": "https://example.com/feed.rss"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```
**Errors:** 400 (Invalid parameters), 404 (No articles found)

### GET /api/articles/{article_id}

**Purpose:** Retrieve a specific article by ID
**Parameters:** 
- `article_id` (int): Article ID
- `include_feed` (bool, optional): Include feed information (default: true)
**Response:** 
```json
{
  "id": 123,
  "feed_id": 45,
  "url": "https://example.com/article",
  "guid": "unique-guid-123",
  "title": "Article Title",
  "summary": "Brief summary",
  "content": "Full article content",
  "author": "Author Name",
  "published_at": "2025-08-16T10:00:00Z",
  "updated_at": "2025-08-16T10:05:00Z",
  "is_read": false,
  "read_at": null,
  "created_at": "2025-08-16T10:10:00Z",
  "feed": {
    "id": 45,
    "title": "Feed Title",
    "url": "https://example.com/feed.rss",
    "category": {
      "id": 10,
      "name": "Technology"
    }
  }
}
```
**Errors:** 404 (Article not found)

### PATCH /api/articles/{article_id}/read-status

**Purpose:** Update the read status of an article
**Parameters:** 
- `article_id` (int): Article ID
**Request Body:**
```json
{
  "is_read": true
}
```
**Response:** 
```json
{
  "id": 123,
  "is_read": true,
  "read_at": "2025-08-16T12:00:00Z"
}
```
**Errors:** 404 (Article not found), 400 (Invalid request body)

### PATCH /api/articles/bulk-read-status

**Purpose:** Update read status for multiple articles
**Parameters:** None
**Request Body:**
```json
{
  "article_ids": [123, 124, 125],
  "is_read": true
}
```
**Response:** 
```json
{
  "updated_count": 3,
  "articles": [
    {
      "id": 123,
      "is_read": true,
      "read_at": "2025-08-16T12:00:00Z"
    },
    {
      "id": 124,
      "is_read": true,
      "read_at": "2025-08-16T12:00:00Z"
    },
    {
      "id": 125,
      "is_read": true,
      "read_at": "2025-08-16T12:00:00Z"
    }
  ]
}
```
**Errors:** 400 (Invalid request body), 404 (Some articles not found)

### POST /api/feeds/{feed_id}/refresh

**Purpose:** Manually trigger a feed refresh
**Parameters:** 
- `feed_id` (int): Feed ID to refresh
- `force` (bool, optional): Force refresh ignoring cache headers (default: false)
**Response:** 
```json
{
  "feed_id": 45,
  "status": "completed",
  "articles_found": 10,
  "articles_new": 3,
  "error_message": null,
  "updated_at": "2025-08-16T12:00:00Z"
}
```
**Errors:** 404 (Feed not found), 500 (Feed fetch error)

### GET /api/feeds/{feed_id}/articles

**Purpose:** Get articles for a specific feed (convenience endpoint)
**Parameters:** 
- `feed_id` (int): Feed ID
- Standard article filtering parameters (page, page_size, is_read, since, until, search)
**Response:** Same as GET /api/articles but filtered to the specific feed
**Errors:** 404 (Feed not found)

### GET /api/categories/{category_id}/articles

**Purpose:** Get articles for all feeds in a specific category
**Parameters:** 
- `category_id` (int): Category ID
- Standard article filtering parameters (page, page_size, is_read, since, until, search)
**Response:** Same as GET /api/articles but filtered to feeds in the category
**Errors:** 404 (Category not found)

### GET /api/articles/stats

**Purpose:** Get reading statistics
**Parameters:** 
- `period` (string, optional): 'day', 'week', 'month', 'year' (default: 'week')
**Response:** 
```json
{
  "total_articles": 1500,
  "unread_articles": 234,
  "read_today": 15,
  "read_this_week": 89,
  "feeds_with_new_articles": 12,
  "most_active_feed": {
    "id": 45,
    "title": "Tech News",
    "new_articles_count": 8
  }
}
```
**Errors:** 400 (Invalid period parameter)

## Controllers

### ArticleController

**Actions:**
- `list_articles()` - Handle article listing with filtering
- `get_article()` - Retrieve single article
- `update_read_status()` - Update single article read status
- `bulk_update_read_status()` - Update multiple articles read status
- `get_article_stats()` - Calculate reading statistics

**Business Logic:**
- Article filtering by multiple criteria
- Pagination with efficient database queries
- Read status tracking with timestamps
- Statistics calculation across time periods

**Error Handling:**
- Validate pagination parameters
- Handle database connection errors
- Return appropriate HTTP status codes
- Log errors for debugging

### FeedRefreshController

**Actions:**
- `refresh_feed()` - Manual feed refresh trigger
- `get_refresh_status()` - Check refresh job status

**Business Logic:**
- Trigger background feed update jobs
- Handle force refresh parameter
- Return immediate status for manual refreshes

**Error Handling:**
- Validate feed existence
- Handle feed parsing errors
- Return detailed error messages for feed issues