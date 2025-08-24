# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-24-async-category-mark-read/spec.md

> Created: 2025-08-24
> Version: 1.0.0

## New Endpoints

### POST /api/articles/bulk/mark-read-by-category/{category_id}

**Purpose:** Start asynchronous bulk mark-as-read operation for all articles in a category
**Parameters:** 
- `category_id` (path): Integer ID of the category
**Response:** 
```json
{
  "job_id": 123,
  "status": "pending",
  "message": "Bulk mark-as-read job created for category 5",
  "estimated_total": 150
}
```
**Errors:** 
- 404: Category not found
- 500: Error creating job

### POST /api/articles/bulk/mark-read-by-feed/{feed_id}

**Purpose:** Start asynchronous bulk mark-as-read operation for all articles in a feed
**Parameters:** 
- `feed_id` (path): Integer ID of the feed
**Response:** 
```json
{
  "job_id": 124,
  "status": "pending", 
  "message": "Bulk mark-as-read job created for feed 12",
  "estimated_total": 45
}
```
**Errors:** 
- 404: Feed not found
- 500: Error creating job

### GET /api/articles/bulk/jobs/{job_id}

**Purpose:** Get current status and progress of a bulk operation job
**Parameters:** 
- `job_id` (path): Integer ID of the job
**Response:** 
```json
{
  "job_id": 123,
  "job_type": "mark_category_read",
  "status": "running",
  "progress": 75,
  "total": 150,
  "created_at": "2025-08-24T10:30:00Z",
  "started_at": "2025-08-24T10:30:02Z",
  "completed_at": null,
  "error_message": null,
  "progress_percentage": 50.0
}
```
**Errors:** 
- 404: Job not found or not accessible by current user

### GET /api/articles/bulk/jobs

**Purpose:** List recent bulk operation jobs for the current user
**Parameters:** 
- `limit` (query, optional): Number of jobs to return (default: 20, max: 100)
- `status` (query, optional): Filter by status ('pending', 'running', 'completed', 'failed')
- `job_type` (query, optional): Filter by job type ('mark_category_read', 'mark_feed_read')
**Response:** 
```json
{
  "jobs": [
    {
      "job_id": 123,
      "job_type": "mark_category_read",
      "status": "completed",
      "progress": 150,
      "total": 150,
      "created_at": "2025-08-24T10:30:00Z",
      "completed_at": "2025-08-24T10:32:15Z",
      "parameters": {"category_id": 5}
    }
  ],
  "total": 1,
  "has_more": false
}
```
**Errors:** None (returns empty list if no jobs)

### DELETE /api/articles/bulk/jobs/{job_id}

**Purpose:** Cancel a pending or running bulk operation job
**Parameters:** 
- `job_id` (path): Integer ID of the job to cancel
**Response:** 
```json
{
  "job_id": 123,
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```
**Errors:** 
- 404: Job not found
- 400: Job cannot be cancelled (already completed or failed)

## Modified Endpoints

### Backward Compatibility for Synchronous Operations

The original synchronous endpoints will remain available for compatibility, but will include warnings about performance:

#### POST /api/articles/bulk/mark-read-by-category/{category_id}?sync=true

**Purpose:** Synchronous bulk mark-as-read (original behavior) - deprecated
**Parameters:** 
- `category_id` (path): Integer ID of the category
- `sync=true` (query): Forces synchronous processing
**Response:** Original `BulkOperationResponse` format
**Notes:** This endpoint will be deprecated and may have timeout issues with large categories

## Response Schemas

### BulkJobResponse
```json
{
  "job_id": "integer",
  "status": "string (enum: pending, running, completed, failed)",
  "message": "string",
  "estimated_total": "integer (optional)"
}
```

### BulkJobStatus
```json
{
  "job_id": "integer",
  "job_type": "string",
  "status": "string (enum: pending, running, completed, failed, cancelled)",
  "progress": "integer",
  "total": "integer", 
  "created_at": "string (ISO datetime)",
  "started_at": "string (ISO datetime, nullable)",
  "completed_at": "string (ISO datetime, nullable)",
  "error_message": "string (nullable)",
  "progress_percentage": "number (0-100)",
  "parameters": "object (job-specific parameters)"
}
```

### BulkJobList
```json
{
  "jobs": "array of BulkJobStatus objects",
  "total": "integer",
  "has_more": "boolean"
}
```

## Job Processing Flow

### Job Lifecycle
1. **Creation**: POST to bulk endpoint creates job in 'pending' status
2. **Processing**: Background worker picks up job, changes status to 'running'
3. **Progress Updates**: Worker periodically updates progress and total fields
4. **Completion**: Job status changes to 'completed' or 'failed'
5. **Cleanup**: Completed jobs are automatically cleaned up after 24 hours

### Error Handling

#### Partial Failures
- Jobs continue processing remaining articles even if some fail
- Progress continues to increment for successful operations
- Final status is 'completed' if most articles succeeded, 'failed' if critical errors

#### Job Cancellation
- Users can cancel pending or running jobs
- Cancellation stops processing but doesn't rollback completed work
- Cancelled jobs are marked with 'cancelled' status

#### Timeout Protection
- Jobs running longer than 1 hour are automatically marked as failed
- Database connection issues cause job restart with progress preservation
- Memory exhaustion protection via batch processing

## Integration Considerations

### Frontend Polling Strategy
- Poll job status every 1-2 seconds during active operations
- Exponential backoff for long-running jobs (decrease polling frequency)
- Stop polling when job reaches terminal state ('completed', 'failed', 'cancelled')

### UI Progress Display
- Show progress bar based on `progress_percentage` field
- Display estimated completion time based on processing rate
- Provide cancel button for pending/running jobs
- Show final result message when job completes

### Performance Characteristics
- Job creation: < 100ms response time
- Status polling: < 50ms response time
- Background processing: 50-100 articles per second
- Memory usage: Constant (batch processing prevents memory growth)