# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-16-backend-api-setup/spec.md

> Created: 2025-08-16
> Version: 1.0.0

## Endpoints

### Feed Management Endpoints

#### GET /api/v1/feeds

**Purpose:** Retrieve list of RSS feeds with optional pagination and filtering
**Parameters:** 
- `limit` (query, optional): Number of feeds to return (default: 20, max: 100)
- `offset` (query, optional): Number of feeds to skip (default: 0)
- `category_id` (query, optional): Filter by category ID
- `is_active` (query, optional): Filter by active status (true/false)

**Response:** 
```json
{
  "feeds": [
    {
      "id": 1,
      "url": "https://example.com/feed.xml",
      "title": "Example Feed",
      "description": "An example RSS feed",
      "category_id": 1,
      "is_active": true,
      "fetch_interval": 3600,
      "last_fetched": "2025-08-16T10:00:00Z",
      "created_at": "2025-08-16T09:00:00Z",
      "updated_at": "2025-08-16T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```
**Errors:** 400 (Invalid parameters), 500 (Server error)

#### POST /api/v1/feeds

**Purpose:** Create a new RSS feed
**Parameters:** Request body with feed data
**Request Body:**
```json
{
  "url": "https://example.com/feed.xml",
  "title": "Example Feed",
  "description": "An example RSS feed",
  "category_id": 1,
  "fetch_interval": 3600
}
```
**Response:** 
```json
{
  "id": 1,
  "url": "https://example.com/feed.xml",
  "title": "Example Feed",
  "description": "An example RSS feed",
  "category_id": 1,
  "is_active": true,
  "fetch_interval": 3600,
  "last_fetched": null,
  "created_at": "2025-08-16T09:00:00Z",
  "updated_at": "2025-08-16T09:00:00Z"
}
```
**Errors:** 400 (Invalid data), 409 (URL already exists), 500 (Server error)

#### GET /api/v1/feeds/{feed_id}

**Purpose:** Retrieve a specific feed by ID
**Parameters:** 
- `feed_id` (path): Feed ID
**Response:** Single feed object (same structure as POST response)
**Errors:** 404 (Feed not found), 500 (Server error)

#### PUT /api/v1/feeds/{feed_id}

**Purpose:** Update an existing feed
**Parameters:** 
- `feed_id` (path): Feed ID
- Request body with updated feed data
**Request Body:** Same as POST (all fields optional)
**Response:** Updated feed object
**Errors:** 400 (Invalid data), 404 (Feed not found), 409 (URL conflict), 500 (Server error)

#### DELETE /api/v1/feeds/{feed_id}

**Purpose:** Delete a feed
**Parameters:** 
- `feed_id` (path): Feed ID
**Response:** 
```json
{
  "message": "Feed deleted successfully"
}
```
**Errors:** 404 (Feed not found), 500 (Server error)

### Category Management Endpoints

#### GET /api/v1/categories

**Purpose:** Retrieve list of all categories
**Parameters:** None
**Response:** 
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Technology",
      "description": "Tech news and articles",
      "color": "#3B82F6",
      "created_at": "2025-08-16T09:00:00Z",
      "updated_at": "2025-08-16T09:00:00Z"
    }
  ]
}
```
**Errors:** 500 (Server error)

#### POST /api/v1/categories

**Purpose:** Create a new category
**Parameters:** Request body with category data
**Request Body:**
```json
{
  "name": "Technology",
  "description": "Tech news and articles",
  "color": "#3B82F6"
}
```
**Response:** Created category object
**Errors:** 400 (Invalid data), 409 (Name already exists), 500 (Server error)

#### GET /api/v1/categories/{category_id}

**Purpose:** Retrieve a specific category by ID
**Parameters:** 
- `category_id` (path): Category ID
**Response:** Single category object
**Errors:** 404 (Category not found), 500 (Server error)

#### PUT /api/v1/categories/{category_id}

**Purpose:** Update an existing category
**Parameters:** 
- `category_id` (path): Category ID
- Request body with updated category data
**Request Body:** Same as POST (all fields optional)
**Response:** Updated category object
**Errors:** 400 (Invalid data), 404 (Category not found), 409 (Name conflict), 500 (Server error)

#### DELETE /api/v1/categories/{category_id}

**Purpose:** Delete a category
**Parameters:** 
- `category_id` (path): Category ID
**Response:** 
```json
{
  "message": "Category deleted successfully"
}
```
**Errors:** 400 (Category has associated feeds), 404 (Category not found), 500 (Server error)

### System Endpoints

#### GET /api/v1/health

**Purpose:** Health check for monitoring
**Parameters:** None
**Response:** 
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-08-16T10:00:00Z"
}
```
**Errors:** 503 (Service unavailable)

## Controllers

### FeedController

**Responsibilities:**
- Handle feed CRUD operations
- Validate feed data using Pydantic models
- Coordinate with FeedService for business logic
- Return appropriate HTTP responses

**Methods:**
- `get_feeds()` - List feeds with pagination
- `create_feed()` - Create new feed
- `get_feed()` - Get feed by ID
- `update_feed()` - Update existing feed
- `delete_feed()` - Delete feed

### CategoryController

**Responsibilities:**
- Handle category CRUD operations
- Validate category data
- Coordinate with CategoryService
- Manage category-feed relationships

**Methods:**
- `get_categories()` - List all categories
- `create_category()` - Create new category
- `get_category()` - Get category by ID
- `update_category()` - Update existing category
- `delete_category()` - Delete category (with dependency check)

### HealthController

**Responsibilities:**
- Provide system health status
- Check database connectivity
- Return monitoring information

**Methods:**
- `health_check()` - Return system status

## Error Response Format

All endpoints return errors in consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid feed URL format",
    "details": {
      "field": "url",
      "value": "invalid-url"
    }
  }
}
```

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `409` - Conflict (duplicate data)
- `500` - Internal Server Error
- `503` - Service Unavailable