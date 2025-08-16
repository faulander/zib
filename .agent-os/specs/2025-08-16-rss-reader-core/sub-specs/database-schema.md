# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-16-rss-reader-core/spec.md

> Created: 2025-08-16
> Version: 1.0.0

## Schema Changes

### New Tables

#### Articles Table

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL,
    url VARCHAR(500) NOT NULL,
    guid VARCHAR(500),
    title VARCHAR(500),
    summary TEXT,
    content TEXT,
    author VARCHAR(255),
    published_at DATETIME,
    updated_at DATETIME,
    is_read BOOLEAN DEFAULT FALSE,
    read_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feed_id) REFERENCES feeds (id) ON DELETE CASCADE,
    UNIQUE (feed_id, url),
    UNIQUE (feed_id, guid)
);
```

#### Feed Update Jobs Table

```sql
CREATE TABLE feed_update_jobs (
    id VARCHAR(50) PRIMARY KEY,
    feed_id INTEGER,
    status VARCHAR(20) DEFAULT 'scheduled',
    started_at DATETIME,
    completed_at DATETIME,
    articles_found INTEGER DEFAULT 0,
    articles_new INTEGER DEFAULT 0,
    error_message TEXT,
    next_run DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feed_id) REFERENCES feeds (id) ON DELETE CASCADE
);
```

### Indexes

#### Articles Table Indexes

```sql
-- Primary lookups
CREATE INDEX idx_articles_feed_id ON articles (feed_id);
CREATE INDEX idx_articles_published_at ON articles (published_at DESC);
CREATE INDEX idx_articles_is_read ON articles (is_read);

-- Composite indexes for common queries
CREATE INDEX idx_articles_feed_read ON articles (feed_id, is_read);
CREATE INDEX idx_articles_feed_published ON articles (feed_id, published_at DESC);
CREATE INDEX idx_articles_read_published ON articles (is_read, published_at DESC);

-- Full-text search support (for future implementation)
CREATE INDEX idx_articles_title ON articles (title);
```

#### Feed Update Jobs Indexes

```sql
CREATE INDEX idx_feed_update_jobs_feed_id ON feed_update_jobs (feed_id);
CREATE INDEX idx_feed_update_jobs_status ON feed_update_jobs (status);
CREATE INDEX idx_feed_update_jobs_next_run ON feed_update_jobs (next_run);
```

### Schema Modifications

#### Feed Table Updates

```sql
-- Add fields to existing feeds table for feed update tracking
ALTER TABLE feeds ADD COLUMN last_successful_fetch DATETIME;
ALTER TABLE feeds ADD COLUMN last_error_message TEXT;
ALTER TABLE feeds ADD COLUMN consecutive_failures INTEGER DEFAULT 0;
ALTER TABLE feeds ADD COLUMN etag VARCHAR(255);
ALTER TABLE feeds ADD COLUMN last_modified VARCHAR(255);
```

## Migration Script

```python
# Migration 003: RSS Reader Core Schema

from peewee import *
from app.core.database import db

def up():
    """Apply the migration"""
    # Create articles table
    db.execute_sql('''
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id INTEGER NOT NULL,
            url VARCHAR(500) NOT NULL,
            guid VARCHAR(500),
            title VARCHAR(500),
            summary TEXT,
            content TEXT,
            author VARCHAR(255),
            published_at DATETIME,
            updated_at DATETIME,
            is_read BOOLEAN DEFAULT FALSE,
            read_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (feed_id) REFERENCES feeds (id) ON DELETE CASCADE
        )
    ''')
    
    # Create feed update jobs table
    db.execute_sql('''
        CREATE TABLE feed_update_jobs (
            id VARCHAR(50) PRIMARY KEY,
            feed_id INTEGER,
            status VARCHAR(20) DEFAULT 'scheduled',
            started_at DATETIME,
            completed_at DATETIME,
            articles_found INTEGER DEFAULT 0,
            articles_new INTEGER DEFAULT 0,
            error_message TEXT,
            next_run DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (feed_id) REFERENCES feeds (id) ON DELETE CASCADE
        )
    ''')
    
    # Add unique constraints
    db.execute_sql('CREATE UNIQUE INDEX idx_articles_feed_url ON articles (feed_id, url)')
    db.execute_sql('CREATE UNIQUE INDEX idx_articles_feed_guid ON articles (feed_id, guid)')
    
    # Create performance indexes
    db.execute_sql('CREATE INDEX idx_articles_feed_id ON articles (feed_id)')
    db.execute_sql('CREATE INDEX idx_articles_published_at ON articles (published_at DESC)')
    db.execute_sql('CREATE INDEX idx_articles_is_read ON articles (is_read)')
    db.execute_sql('CREATE INDEX idx_articles_feed_read ON articles (feed_id, is_read)')
    db.execute_sql('CREATE INDEX idx_articles_feed_published ON articles (feed_id, published_at DESC)')
    db.execute_sql('CREATE INDEX idx_articles_read_published ON articles (is_read, published_at DESC)')
    
    # Feed update jobs indexes
    db.execute_sql('CREATE INDEX idx_feed_update_jobs_feed_id ON feed_update_jobs (feed_id)')
    db.execute_sql('CREATE INDEX idx_feed_update_jobs_status ON feed_update_jobs (status)')
    db.execute_sql('CREATE INDEX idx_feed_update_jobs_next_run ON feed_update_jobs (next_run)')
    
    # Add new columns to feeds table
    db.execute_sql('ALTER TABLE feeds ADD COLUMN last_successful_fetch DATETIME')
    db.execute_sql('ALTER TABLE feeds ADD COLUMN last_error_message TEXT')
    db.execute_sql('ALTER TABLE feeds ADD COLUMN consecutive_failures INTEGER DEFAULT 0')
    db.execute_sql('ALTER TABLE feeds ADD COLUMN etag VARCHAR(255)')
    db.execute_sql('ALTER TABLE feeds ADD COLUMN last_modified VARCHAR(255)')

def down():
    """Reverse the migration"""
    db.execute_sql('DROP TABLE IF EXISTS articles')
    db.execute_sql('DROP TABLE IF EXISTS feed_update_jobs')
    
    # Note: SQLite doesn't support DROP COLUMN, so feed table changes are permanent
```

## Rationale

**Article URL + GUID Uniqueness**: Using both URL and GUID ensures we handle feeds that might change URLs or use GUIDs inconsistently, preventing duplicate articles while maintaining feed compatibility.

**Composite Indexes**: The combination of feed_id with is_read and published_at supports the most common query patterns (recent unread articles, articles by feed, etc.) for optimal performance.

**Feed Update Tracking**: Storing ETags and Last-Modified headers enables efficient conditional requests, reducing bandwidth and server load while ensuring we don't miss updates.

**Cascade Deletion**: When a feed is deleted, all its articles and update jobs are automatically removed, maintaining data consistency.