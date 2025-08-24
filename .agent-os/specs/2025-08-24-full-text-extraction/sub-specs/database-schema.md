# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-24-full-text-extraction/spec.md

> Created: 2025-08-24
> Version: 1.0.0

## Changes

### New Columns for Article Table

Add the following columns to the existing `Article` model:

- `full_text_content` - TEXT field for storing extracted article content
- `extraction_status` - VARCHAR(20) with enum values: 'pending', 'success', 'failed', 'skipped'
- `extraction_attempted_at` - TIMESTAMP for tracking when extraction was last attempted
- `extraction_error` - TEXT field for storing error messages from failed extractions

### New Table: extraction_jobs

Create a queue table for managing background extraction jobs:

```sql
CREATE TABLE extraction_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    completed_at TEXT,
    error_message TEXT,
    FOREIGN KEY (article_id) REFERENCES articles (id) ON DELETE CASCADE
);

CREATE INDEX idx_extraction_jobs_status ON extraction_jobs (status);
CREATE INDEX idx_extraction_jobs_scheduled ON extraction_jobs (scheduled_at);
CREATE INDEX idx_extraction_jobs_article ON extraction_jobs (article_id);
```

## Migration SQL

```sql
-- Migration: Add full text extraction fields to articles table
ALTER TABLE articles ADD COLUMN full_text_content TEXT;
ALTER TABLE articles ADD COLUMN extraction_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE articles ADD COLUMN extraction_attempted_at TEXT;
ALTER TABLE articles ADD COLUMN extraction_error TEXT;

-- Create extraction jobs queue table
CREATE TABLE extraction_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    completed_at TEXT,
    error_message TEXT,
    FOREIGN KEY (article_id) REFERENCES articles (id) ON DELETE CASCADE
);

CREATE INDEX idx_extraction_jobs_status ON extraction_jobs (status);
CREATE INDEX idx_extraction_jobs_scheduled ON extraction_jobs (scheduled_at);
CREATE INDEX idx_extraction_jobs_article ON extraction_jobs (article_id);
```

## Rationale

### Article Table Extensions
- `full_text_content` stores the complete extracted text separately from RSS content
- `extraction_status` enables efficient querying of articles by extraction state
- `extraction_attempted_at` supports retry logic with exponential backoff
- `extraction_error` helps debug and monitor extraction failures

### Extraction Jobs Table
- Provides a persistent queue for background processing
- `priority` allows prioritizing certain articles (e.g., recently published)
- `attempts` enables retry limits to prevent infinite retry loops
- `scheduled_at` supports delayed retry scheduling
- Foreign key with CASCADE ensures cleanup when articles are deleted

### Indexing Strategy
- Status index enables efficient querying of pending jobs
- Scheduled index supports time-based job processing
- Article index enables quick lookup of jobs for specific articles

## Data Integrity

- Articles can exist without extracted content (extraction_status = 'pending' or 'failed')
- Extraction jobs are automatically cleaned up when articles are deleted
- Timestamps use TEXT format consistent with existing pendulum usage
- Enum values for extraction_status provide clear state management