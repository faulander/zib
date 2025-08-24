# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-24-async-category-mark-read/spec.md

> Created: 2025-08-24
> Version: 1.0.0

## Changes

### New Table: bulk_operation_jobs

Create a new table to track background bulk operation jobs:

```sql
CREATE TABLE bulk_operation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    user_id INTEGER NOT NULL,
    parameters TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_bulk_jobs_user_status ON bulk_operation_jobs (user_id, status);
CREATE INDEX idx_bulk_jobs_created ON bulk_operation_jobs (created_at);
CREATE INDEX idx_bulk_jobs_type_status ON bulk_operation_jobs (job_type, status);
```

## Migration SQL

```sql
-- Migration: Add bulk operation jobs table for async processing
CREATE TABLE bulk_operation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    user_id INTEGER NOT NULL,
    parameters TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Create indexes for efficient querying
CREATE INDEX idx_bulk_jobs_user_status ON bulk_operation_jobs (user_id, status);
CREATE INDEX idx_bulk_jobs_created ON bulk_operation_jobs (created_at);
CREATE INDEX idx_bulk_jobs_type_status ON bulk_operation_jobs (job_type, status);
```

## Field Descriptions

### bulk_operation_jobs Table

- **id**: Primary key for the job
- **job_type**: Type of bulk operation ('mark_category_read', 'mark_feed_read', etc.)
- **status**: Current job status ('pending', 'running', 'completed', 'failed')
- **user_id**: Foreign key to the user who initiated the job
- **parameters**: JSON string containing job parameters (category_id, feed_id, etc.)
- **progress**: Number of items processed so far
- **total**: Total number of items to process
- **created_at**: When the job was created (UTC timestamp)
- **started_at**: When the job started processing (UTC timestamp)
- **completed_at**: When the job finished (UTC timestamp)
- **error_message**: Error details if the job failed

## Job Status Enum Values

- **pending**: Job created but not yet started
- **running**: Job is currently being processed
- **completed**: Job finished successfully
- **failed**: Job encountered an error and stopped

## Job Type Enum Values

- **mark_category_read**: Mark all articles in a category as read
- **mark_feed_read**: Mark all articles in a feed as read
- **mark_all_read**: Mark all articles for a user as read

## Indexing Strategy

### Performance Indexes
- **user_status index**: Enables fast queries for user's active jobs
- **created index**: Supports job cleanup and sorting by creation time
- **type_status index**: Allows efficient filtering by job type and status

### Query Patterns Supported
- Find all jobs for a user: `WHERE user_id = ?`
- Find active jobs for monitoring: `WHERE status IN ('pending', 'running')`
- Find jobs needing cleanup: `WHERE created_at < ? AND status IN ('completed', 'failed')`
- Find specific job types: `WHERE job_type = ? AND status = ?`

## Data Cleanup Strategy

### Automatic Cleanup
```sql
-- Clean up completed jobs older than 24 hours
DELETE FROM bulk_operation_jobs 
WHERE status IN ('completed', 'failed') 
AND created_at < datetime('now', '-1 day');

-- Clean up abandoned jobs older than 1 hour
UPDATE bulk_operation_jobs 
SET status = 'failed', 
    error_message = 'Job abandoned due to timeout',
    completed_at = datetime('now')
WHERE status = 'running' 
AND started_at < datetime('now', '-1 hour');
```

## Foreign Key Relationships

- **user_id**: References users table with CASCADE DELETE to clean up jobs when user is deleted
- Jobs are user-scoped and automatically cleaned up if user account is removed

## Storage Considerations

- **parameters field**: Stores JSON data for job configuration, allowing flexible parameter passing
- **TEXT fields**: Use TEXT type for timestamps to maintain consistency with existing pendulum usage
- **INTEGER progress/total**: Use integers for progress tracking to avoid floating point precision issues

## Migration Dependencies

- Requires existing users table
- Should be applied after all user authentication migrations
- Compatible with existing SQLite database structure