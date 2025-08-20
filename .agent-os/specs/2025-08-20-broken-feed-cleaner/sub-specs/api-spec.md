# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-20-broken-feed-cleaner/spec.md

> Created: 2025-08-20
> Version: 1.0.0

## Endpoints

### POST /api/feeds/check-category/{category_id}

**Purpose:** Initiate feed accessibility checking for all feeds in a category
**Parameters:** 
- `category_id` (path): ID of the category to check
**Response:** 
```json
{
  "session_id": "uuid-string",
  "message": "Feed checking started",
  "total_feeds": 12,
  "estimated_duration": "30 seconds"
}
```
**Errors:** 
- 404: Category not found
- 400: Invalid category ID

### GET /api/feeds/check-status/{session_id}

**Purpose:** Get progress status of ongoing feed check operation
**Parameters:** 
- `session_id` (path): Session ID returned from check-category endpoint
**Response:** 
```json
{
  "session_id": "uuid-string",
  "status": "running",
  "progress": {
    "completed": 8,
    "total": 12,
    "current_feed": "Tech News RSS",
    "percentage": 67
  },
  "results": {
    "accessible": 6,
    "inaccessible": 2,
    "pending": 4
  }
}
```
**Errors:** 
- 404: Session not found
- 410: Session expired

### GET /api/feeds/broken/{category_id}

**Purpose:** Get list of feeds that have been inaccessible for 7+ days
**Parameters:** 
- `category_id` (path): ID of the category to check for broken feeds
- `days` (query, optional): Number of days threshold (default: 7)
**Response:** 
```json
{
  "broken_feeds": [
    {
      "id": 123,
      "title": "Broken Tech News",
      "url": "https://example.com/rss.xml",
      "last_checked": "2025-08-13T10:30:00Z",
      "consecutive_failures": 15,
      "last_success": "2025-08-10T14:20:00Z",
      "recent_errors": [
        {
          "checked_at": "2025-08-13T10:30:00Z",
          "error_message": "Connection timeout",
          "status_code": null
        }
      ]
    }
  ],
  "total_broken": 1,
  "category_name": "Technology"
}
```
**Errors:** 
- 404: Category not found

### DELETE /api/feeds/bulk-delete

**Purpose:** Delete multiple feeds in a single operation
**Parameters:** 
- Request body: `{"feed_ids": [123, 456, 789]}`
**Response:** 
```json
{
  "deleted_count": 2,
  "failed_deletions": [
    {
      "feed_id": 789,
      "error": "Feed not found"
    }
  ],
  "message": "Successfully deleted 2 of 3 feeds"
}
```
**Errors:** 
- 400: Invalid request body or no feed IDs provided

### GET /api/feeds/{feed_id}/check-history

**Purpose:** Get detailed check history for a specific feed
**Parameters:** 
- `feed_id` (path): ID of the feed
- `limit` (query, optional): Number of history entries to return (default: 20)
**Response:** 
```json
{
  "feed_id": 123,
  "feed_title": "Tech News RSS",
  "check_history": [
    {
      "checked_at": "2025-08-20T10:30:00Z",
      "is_success": false,
      "status_code": null,
      "error_message": "Connection timeout",
      "response_time_ms": 10000
    },
    {
      "checked_at": "2025-08-19T10:30:00Z",
      "is_success": true,
      "status_code": 200,
      "error_message": null,
      "response_time_ms": 850
    }
  ],
  "total_checks": 45,
  "success_rate": 0.75
}
```
**Errors:** 
- 404: Feed not found

## Controllers

### FeedHealthController

**check_category_feeds(category_id)**
- Create unique session ID for tracking
- Query all accessible feeds in category
- Start background task for async checking
- Return session details immediately

**get_check_status(session_id)**
- Lookup session in memory/cache
- Return current progress and results
- Clean up completed sessions after 5 minutes

**get_broken_feeds(category_id, days_threshold)**
- Query feeds with last_checked older than threshold
- Include recent error history for each feed
- Calculate consecutive failure counts
- Return structured broken feeds list

**bulk_delete_feeds(feed_ids)**
- Validate all feed IDs exist
- Delete feeds and related data (articles, logs)
- Track success/failure for each deletion
- Return detailed results

**get_feed_check_history(feed_id, limit)**
- Query feed_check_logs table for feed
- Calculate success rate statistics
- Return paginated history with metadata

## Background Task Implementation

### Feed Check Session Manager

```python
class FeedCheckSession:
    def __init__(self, session_id, category_id, feed_ids):
        self.session_id = session_id
        self.category_id = category_id
        self.feed_ids = feed_ids
        self.completed = 0
        self.results = {"accessible": 0, "inaccessible": 0}
        self.status = "running"
        self.current_feed = None
        
    async def check_all_feeds(self):
        for feed_id in self.feed_ids:
            await self.check_single_feed(feed_id)
            self.completed += 1
        self.status = "completed"
```

### Feed Connectivity Checker

```python
async def check_feed_accessibility(feed_url: str) -> FeedCheckResult:
    """Check if feed URL is accessible"""
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.head(feed_url)
            response_time = int((time.time() - start_time) * 1000)
            return FeedCheckResult(
                success=response.status_code < 400,
                status_code=response.status_code,
                response_time_ms=response_time
            )
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return FeedCheckResult(
            success=False,
            error_message=str(e),
            response_time_ms=response_time
        )
```

## Session Management

- **In-Memory Storage**: Active sessions stored in application memory with automatic cleanup
- **Session Expiry**: Sessions expire after 5 minutes of completion to prevent memory leaks
- **Concurrent Sessions**: Multiple categories can be checked simultaneously
- **Progress Tracking**: Real-time progress updates through session status endpoint