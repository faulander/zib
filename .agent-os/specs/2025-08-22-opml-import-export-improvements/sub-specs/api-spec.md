# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-22-opml-import-export-improvements/spec.md

> Created: 2025-08-22
> Version: 1.0.0

## New Endpoints

### WebSocket Endpoint for Import Progress

**WebSocket** `/ws/import/{job_id}`

**Purpose:** Real-time progress updates for OPML import jobs
**Parameters:** 
- `job_id`: Import job identifier
**Response:** JSON progress updates
**Connection:** Authenticated WebSocket connection

**Message Format:**
```json
{
  "job_id": "imp_abc123def456",
  "status": "processing",
  "current_phase": "importing_feeds", 
  "phase_description": "Importing RSS feeds",
  "current_step": 45,
  "total_steps": 200,
  "progress_percentage": 22.5,
  "categories_created": 8,
  "feeds_imported": 45,
  "feeds_failed": 2,
  "duplicates_found": 3,
  "eta_seconds": 120,
  "current_item": "Tech News Feed"
}
```

**Error Handling:**
- Connection drops on job completion/failure
- Sends error messages for job failures
- Handles client disconnection gracefully

### OPML Export Endpoint

**GET** `/api/export/opml`

**Purpose:** Export feeds and categories as OPML file
**Parameters:** 
- `category_ids`: Optional comma-separated category IDs to export
- `include_all`: Boolean, export all feeds (default: true)
- `format`: Export format, "opml" (default)
**Response:** OPML XML file download
**Content-Type:** `application/xml`
**Headers:** `Content-Disposition: attachment; filename="feeds.opml"`

**Query Parameters:**
```
GET /api/export/opml?category_ids=1,3,5&include_all=false
```

**Response Headers:**
```
Content-Type: application/xml
Content-Disposition: attachment; filename="zib_feeds_2025-08-22.opml"
Content-Length: 15420
```

**Error Responses:**
- `400 Bad Request`: Invalid category IDs or parameters
- `404 Not Found`: No feeds found matching criteria
- `500 Internal Server Error`: Export generation failed

### Export Options Endpoint

**GET** `/api/export/options`

**Purpose:** Get available export options and feed/category counts
**Parameters:** None
**Response:** JSON with export options and statistics

**Response Format:**
```json
{
  "total_feeds": 185,
  "total_categories": 12,
  "categories": [
    {
      "id": 1,
      "name": "Technology",
      "feed_count": 23
    },
    {
      "id": 2, 
      "name": "News",
      "feed_count": 45
    }
  ],
  "estimated_file_size_kb": 156
}
```

## Enhanced Existing Endpoints

### Import Job Status Enhancement

**GET** `/api/import/jobs/{job_id}`

**Enhanced Response:** Added fields for better progress tracking

**New Fields:**
```json
{
  "eta_seconds": 120,
  "current_item": "Processing: Tech News Feed",
  "phase_description": "Importing RSS feeds (45 of 200)",
  "validation_errors": [
    {
      "feed_title": "Broken Feed",
      "feed_url": "https://example.com/broken.xml", 
      "error": "Connection timeout after 30 seconds"
    }
  ],
  "performance_metrics": {
    "feeds_per_second": 2.3,
    "estimated_completion": "2025-08-22T12:35:00Z"
  }
}
```

### Import Job Creation Enhancement

**POST** `/api/import/opml`

**Enhanced Options:** Added performance and progress options

**New Form Parameters:**
```json
{
  "enable_concurrent_validation": true,
  "concurrent_limit": 10,
  "batch_size": 50,
  "progress_update_interval": 10,
  "skip_validation_on_timeout": true,
  "validation_timeout_seconds": 30
}
```

## WebSocket Protocol

### Connection Establishment

1. Client establishes WebSocket connection to `/ws/import/{job_id}`
2. Server validates job ownership and authentication
3. Server sends initial progress state
4. Server streams progress updates until job completion

### Message Types

**Progress Update:**
```json
{
  "type": "progress",
  "data": { /* progress object */ }
}
```

**Status Change:**
```json
{
  "type": "status", 
  "data": {
    "job_id": "imp_abc123",
    "old_status": "processing",
    "new_status": "completed"
  }
}
```

**Error Message:**
```json
{
  "type": "error",
  "data": {
    "job_id": "imp_abc123",
    "error": "Feed validation failed",
    "details": "Connection timeout for feed: https://example.com/rss"
  }
}
```

**Completion Message:**
```json
{
  "type": "complete",
  "data": {
    "job_id": "imp_abc123", 
    "summary": {
      "feeds_imported": 185,
      "categories_created": 12,
      "feeds_failed": 3,
      "duplicates_skipped": 5,
      "total_duration_seconds": 87
    }
  }
}
```

## Controllers

### ImportWebSocketController

**Purpose:** Handle WebSocket connections for import progress
**Methods:**
- `connect()`: Establish WebSocket connection with authentication
- `disconnect()`: Clean up connection and resources
- `send_progress()`: Send progress updates to connected clients
- `handle_job_completion()`: Send final results and close connection

### ExportController  

**Purpose:** Handle OPML export requests
**Methods:**
- `export_opml()`: Generate and stream OPML file
- `get_export_options()`: Return available export options
- `validate_export_params()`: Validate export parameters
- `generate_filename()`: Create timestamped filename

### Enhanced ImportController

**Purpose:** Enhanced import job management
**New Methods:**
- `get_performance_metrics()`: Calculate import performance statistics
- `estimate_completion_time()`: Provide ETA based on current progress
- `get_validation_errors()`: Return detailed validation error information

## Integration Points

### Frontend Integration

1. **Progress Modal**: Connects to WebSocket endpoint for real-time updates
2. **Export Button**: Triggers OPML export with optional filtering
3. **Settings Page**: Integrates export options and import preferences

### Background Services Integration

1. **Import Service**: Enhanced with WebSocket progress broadcasting
2. **Export Service**: New service for OPML generation
3. **Job Manager**: Enhanced with performance tracking and WebSocket notifications

## Authentication & Authorization

- **WebSocket**: Requires valid user session, validates job ownership
- **Export**: Requires authentication, only exports user's own feeds
- **Import**: Existing authentication requirements maintained

## Error Handling

- **Connection Failures**: Graceful degradation to polling-based updates
- **Export Errors**: Detailed error messages with suggested fixes
- **Import Failures**: Continue processing with detailed error reporting
- **Resource Limits**: Handle large exports with streaming and memory management