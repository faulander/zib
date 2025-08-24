# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-24-full-text-extraction/spec.md

> Created: 2025-08-24
> Version: 1.0.0

## Endpoints

### GET /api/articles/{article_id}/full-text

**Purpose:** Retrieve the full extracted text content for a specific article
**Parameters:** 
- `article_id` (path): Integer ID of the article
**Response:** 
```json
{
  "article_id": 123,
  "has_full_text": true,
  "extraction_status": "success",
  "full_text_content": "Complete extracted article text...",
  "extracted_at": "2025-08-24T10:30:00Z",
  "extraction_error": null
}
```
**Errors:** 
- 404: Article not found
- 200: Always returns, with has_full_text=false if extraction failed/pending

### POST /api/articles/{article_id}/extract

**Purpose:** Manually trigger full-text extraction for a specific article
**Parameters:** 
- `article_id` (path): Integer ID of the article
- `force` (query, optional): Boolean to force re-extraction even if already successful
**Response:** 
```json
{
  "article_id": 123,
  "job_id": 456,
  "status": "queued",
  "message": "Extraction job queued successfully"
}
```
**Errors:** 
- 404: Article not found
- 429: Too many extraction requests (rate limited)

### GET /api/extraction/status

**Purpose:** Get overall extraction queue status and statistics
**Parameters:** None
**Response:** 
```json
{
  "pending_jobs": 15,
  "failed_jobs": 3,
  "total_extracted": 1247,
  "extraction_success_rate": 0.87,
  "worker_status": "running"
}
```
**Errors:** None (always returns current status)

### POST /api/extraction/start

**Purpose:** Start the background extraction worker
**Parameters:** None
**Response:** 
```json
{
  "status": "started",
  "message": "Background extraction worker started"
}
```
**Errors:** 
- 409: Worker already running

### POST /api/extraction/stop

**Purpose:** Stop the background extraction worker
**Parameters:** None
**Response:** 
```json
{
  "status": "stopped",
  "message": "Background extraction worker stopped"
}
```
**Errors:** None (idempotent operation)

### GET /api/extraction/jobs

**Purpose:** List recent extraction jobs with their status
**Parameters:** 
- `limit` (query, optional): Number of jobs to return (default: 50, max: 200)
- `status` (query, optional): Filter by status ('pending', 'success', 'failed')
**Response:** 
```json
{
  "jobs": [
    {
      "id": 456,
      "article_id": 123,
      "status": "success",
      "attempts": 1,
      "created_at": "2025-08-24T10:30:00Z",
      "completed_at": "2025-08-24T10:31:15Z",
      "error_message": null
    }
  ],
  "total": 1,
  "has_more": false
}
```
**Errors:** None

## Integration with Existing APIs

### Modified Article Endpoints

The existing article endpoints will be enhanced to include extraction information:

#### GET /api/articles/

Add extraction fields to article response:
```json
{
  "id": 123,
  "title": "Article Title",
  "content": "Original RSS content...",
  "has_full_text": true,
  "extraction_status": "success",
  // ... other existing fields
}
```

#### GET /api/articles/{article_id}

Include full extraction details in single article response:
```json
{
  "id": 123,
  "title": "Article Title",
  "content": "Original RSS content...",
  "full_text_content": "Complete extracted text...",
  "extraction_status": "success",
  "extracted_at": "2025-08-24T10:30:00Z",
  // ... other existing fields
}
```

## Background Processing Integration

### RSS Feed Processing
- When new articles are added during RSS feed updates, automatically create extraction jobs
- Do not block RSS processing for extraction - jobs are queued asynchronously
- Articles are immediately available with original RSS content

### Job Processing
- Background worker processes extraction jobs in order of priority and creation time
- Implements exponential backoff for retry attempts
- Respects rate limits to avoid overwhelming target websites
- Updates article records with extracted content and status

## Error Handling

- **Network failures**: Retry with exponential backoff (max 3 attempts)
- **Parsing failures**: Mark as failed with error details, do not retry
- **Rate limiting**: Implement delays and respect HTTP 429 responses
- **Timeouts**: 30-second timeout per extraction attempt
- **Invalid URLs**: Skip extraction and mark as 'skipped'

## Security Considerations

- Rate limiting on manual extraction endpoints to prevent abuse
- Validate article ownership/access before allowing extraction
- Sanitize URLs before passing to newspaper4k
- Log extraction requests for monitoring and debugging