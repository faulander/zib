# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-16-opml-import-feature/spec.md

> Created: 2025-08-16
> Version: 1.0.0

## Endpoints

### POST /api/opml/import

**Purpose:** Upload and initiate OPML import process
**Content-Type:** multipart/form-data
**Authentication:** Required

**Parameters:**
- `file` (required): OPML file upload (max 10MB)
- `duplicate_strategy` (optional): "skip" | "update" | "merge" | "prompt" (default: "skip")
- `category_parent_id` (optional): Parent category ID for imported categories (default: root)
- `validate_feeds` (optional): boolean to enable/disable feed URL validation (default: true)

**Response 200:**
```json
{
  "import_id": "imp_abc123def456",
  "status": "started",
  "message": "OPML import initiated successfully",
  "estimated_feeds": 142,
  "estimated_categories": 18
}
```

**Response 400:**
```json
{
  "error": "invalid_file",
  "message": "Invalid OPML file format",
  "details": "XML parsing error at line 23: unexpected end of file"
}
```

**Errors:**
- 400: Invalid file format, file too large, invalid parameters
- 401: Authentication required
- 429: Too many concurrent imports
- 500: Internal server error

### GET /api/opml/import/{import_id}/status

**Purpose:** Get current import progress and status
**Authentication:** Required

**Parameters:**
- `import_id` (path): Import job identifier

**Response 200:**
```json
{
  "import_id": "imp_abc123def456",
  "status": "processing",
  "progress": {
    "phase": "validating_feeds",
    "current_step": 45,
    "total_steps": 142,
    "percentage": 32
  },
  "stats": {
    "categories_created": 12,
    "feeds_imported": 38,
    "feeds_failed": 2,
    "duplicates_found": 5
  },
  "estimated_completion": "2025-08-16T14:30:00Z"
}
```

**Response 404:**
```json
{
  "error": "import_not_found",
  "message": "Import job not found or expired"
}
```

**Errors:**
- 404: Import ID not found or expired
- 401: Authentication required or import belongs to different user

### GET /api/opml/import/{import_id}/result

**Purpose:** Get final import results and summary
**Authentication:** Required

**Parameters:**
- `import_id` (path): Import job identifier

**Response 200 (Success):**
```json
{
  "import_id": "imp_abc123def456",
  "status": "completed",
  "summary": {
    "total_feeds": 142,
    "feeds_imported": 128,
    "feeds_failed": 14,
    "categories_created": 18,
    "duplicates_handled": 12,
    "processing_time_seconds": 45
  },
  "results": {
    "categories": [
      {
        "name": "Technology",
        "id": 15,
        "feeds_count": 23,
        "parent_path": "/Technology"
      }
    ],
    "successful_feeds": [
      {
        "title": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "category_id": 15,
        "feed_id": 89
      }
    ],
    "failed_feeds": [
      {
        "title": "Broken Feed",
        "url": "https://example.com/feed.xml",
        "error": "404 Not Found",
        "error_code": "feed_not_found"
      }
    ],
    "duplicates": [
      {
        "title": "Existing Feed",
        "url": "https://feeds.example.com/news",
        "action": "skipped",
        "existing_feed_id": 42
      }
    ]
  }
}
```

**Response 200 (In Progress):**
```json
{
  "import_id": "imp_abc123def456",
  "status": "processing",
  "message": "Import still in progress. Use /status endpoint for updates."
}
```

**Errors:**
- 404: Import ID not found or expired
- 401: Authentication required or import belongs to different user

### DELETE /api/opml/import/{import_id}

**Purpose:** Cancel ongoing import or clean up completed import
**Authentication:** Required

**Parameters:**
- `import_id` (path): Import job identifier

**Response 200:**
```json
{
  "import_id": "imp_abc123def456",
  "status": "cancelled",
  "message": "Import job cancelled successfully"
}
```

**Response 404:**
```json
{
  "error": "import_not_found",
  "message": "Import job not found or already completed"
}
```

**Errors:**
- 404: Import ID not found
- 401: Authentication required or import belongs to different user
- 409: Import already completed, cannot cancel

### GET /api/opml/import/history

**Purpose:** Get user's import history
**Authentication:** Required

**Parameters:**
- `limit` (query, optional): Number of imports to return (default: 20, max: 100)
- `offset` (query, optional): Pagination offset (default: 0)

**Response 200:**
```json
{
  "imports": [
    {
      "import_id": "imp_abc123def456",
      "status": "completed",
      "created_at": "2025-08-16T14:00:00Z",
      "completed_at": "2025-08-16T14:01:30Z",
      "filename": "my_feeds.opml",
      "summary": {
        "feeds_imported": 128,
        "categories_created": 18
      }
    }
  ],
  "total": 5,
  "has_more": false
}
```

**Errors:**
- 401: Authentication required

## Controllers

### OPMLImportController

**upload_opml()**
- Validate uploaded file format and size
- Parse OPML structure for initial analysis
- Create import job record in database
- Queue asynchronous import processing
- Return import ID and initial estimates

**get_import_status()**
- Retrieve import job from database
- Calculate current progress based on completed steps
- Return real-time status and progress information
- Handle import job expiration

**get_import_result()**
- Retrieve completed import results
- Format detailed success/failure summary
- Include actionable information for failed imports
- Return comprehensive import statistics

**cancel_import()**
- Mark import job as cancelled
- Clean up temporary data and resources
- Stop ongoing processing if possible
- Return cancellation confirmation

**get_import_history()**
- Retrieve user's import history with pagination
- Filter and sort by creation date
- Include summary statistics for each import
- Support pagination for large import histories

### OPMLProcessorService

**process_opml_async()**
- Background task for processing OPML imports
- Parse OPML XML structure into categories and feeds
- Create category hierarchy with duplicate handling
- Validate and import feeds with progress tracking
- Generate comprehensive import results and statistics

**validate_feed_url()**
- Perform HTTP HEAD request to validate feed URL
- Handle redirects and extract final feed URL
- Parse feed metadata for title and description
- Return validation results with error details

**handle_duplicates()**
- Detect duplicate feeds and categories
- Apply user-specified duplicate handling strategy
- Track duplicate handling decisions for reporting
- Ensure data consistency during merge operations