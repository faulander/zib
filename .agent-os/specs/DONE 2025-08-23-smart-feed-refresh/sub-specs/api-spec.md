# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-23-smart-feed-refresh/spec.md

> Created: 2025-08-23
> Version: 1.0.0

## New API Endpoints

### GET /api/feeds/priority-status

**Purpose:** Get current priority scores and refresh status for all feeds
**Parameters:** None
**Response:** 
```json
{
  "feeds": [
    {
      "id": 1,
      "title": "Tech News",
      "priority_score": 8.5,
      "last_post_date": "2025-08-23T10:30:00Z",
      "posting_frequency_days": 0.5,
      "consecutive_failures": 0,
      "refresh_status": "pending|refreshing|completed|failed"
    }
  ],
  "refresh_in_progress": true,
  "estimated_completion": "2025-08-23T11:15:00Z"
}
```
**Errors:** 500 on database errors

### POST /api/feeds/refresh/smart

**Purpose:** Trigger smart priority-based refresh cycle
**Parameters:** 
```json
{
  "batch_size": 10,
  "force_recalculate_priorities": false
}
```
**Response:**
```json
{
  "message": "Smart refresh started",
  "feeds_queued": 45,
  "estimated_duration_minutes": 12,
  "refresh_id": "refresh_2025082311"
}
```
**Errors:** 409 if refresh already in progress, 500 on system errors

### GET /api/feeds/refresh/status/{refresh_id}

**Purpose:** Get status of ongoing smart refresh operation
**Parameters:** refresh_id (path parameter)
**Response:**
```json
{
  "refresh_id": "refresh_2025082311",
  "status": "in_progress|completed|failed",
  "feeds_processed": 23,
  "feeds_total": 45,
  "current_feed": "Tech News",
  "started_at": "2025-08-23T11:00:00Z",
  "estimated_completion": "2025-08-23T11:15:00Z",
  "errors": []
}
```

## Modified Endpoints

### POST /api/feeds/refresh-all (Enhanced)

Add smart refresh option to existing endpoint:

**Parameters:**
```json
{
  "use_smart_refresh": true,
  "batch_size": 10
}
```

**Response:** Same as existing but includes priority information when smart refresh is used

## Backend Controllers

### SmartRefreshController

**Actions:**
- `start_smart_refresh()` - Initialize priority-based refresh cycle
- `get_refresh_status()` - Return current refresh progress
- `get_feed_priorities()` - Return calculated feed priorities
- `pause_refresh()` - Pause ongoing refresh (for maintenance)
- `resume_refresh()` - Resume paused refresh

**Business Logic:**
- Calculate priority scores using multiple factors
- Queue feeds in priority order
- Process feeds sequentially with configurable delays
- Handle individual feed failures gracefully
- Update refresh status in real-time

**Error Handling:**
- Failed feed refresh doesn't block other feeds
- Exponential backoff for repeatedly failing feeds
- Graceful degradation to standard refresh if smart refresh fails
- Comprehensive logging for debugging and optimization

## Integration Points

### Frontend Integration
- Replace `apiActions.refreshAllFeeds()` calls with smart refresh option
- Add progress indicators for ongoing smart refresh operations  
- Display feed priorities in admin/debug interface (optional)

### Auto-Refresh Service Integration
```python
# In autoRefreshService._refreshArticles()
if settings.use_smart_refresh:
    await apiActions.startSmartRefresh()
else:
    await apiActions.refreshAllFeeds()  # Fallback
```