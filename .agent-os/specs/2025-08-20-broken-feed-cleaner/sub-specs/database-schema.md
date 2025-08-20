# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-20-broken-feed-cleaner/spec.md

> Created: 2025-08-20
> Version: 1.0.0

## Schema Changes

### Extend Existing Feeds Table

Add new columns to track feed accessibility:

```sql
-- Add accessibility tracking columns to feeds table
ALTER TABLE feeds ADD COLUMN last_checked DATETIME;
ALTER TABLE feeds ADD COLUMN accessible BOOLEAN DEFAULT true;
ALTER TABLE feeds ADD COLUMN consecutive_failures INTEGER DEFAULT 0;
```

### New Feed Check Logs Table

Create comprehensive logging table for feed check history:

```sql
-- Create feed check logs table
CREATE TABLE feed_check_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL,
    checked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_code INTEGER,
    error_message TEXT,
    response_time_ms INTEGER,
    is_success BOOLEAN NOT NULL,
    user_agent TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feed_id) REFERENCES feeds (id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_feed_check_logs_feed_id ON feed_check_logs(feed_id);
CREATE INDEX idx_feed_check_logs_checked_at ON feed_check_logs(checked_at);
CREATE INDEX idx_feed_check_logs_success ON feed_check_logs(is_success);
```

### Migration Implementation

Using Peewee migration system:

```python
# Migration file: migrations/add_feed_health_tracking.py

from peewee import *
from app.core.database import database

def migrate():
    """Add feed health tracking columns and create check logs table"""
    
    # Add columns to feeds table
    migrator = SqliteMigrator(database)
    
    migrate(
        migrator.add_column('feeds', 'last_checked', DateTimeField(null=True)),
        migrator.add_column('feeds', 'accessible', BooleanField(default=True)),
        migrator.add_column('feeds', 'consecutive_failures', IntegerField(default=0)),
    )
    
    # Create feed check logs table
    class FeedCheckLog(Model):
        id = AutoField(primary_key=True)
        feed_id = IntegerField()
        checked_at = DateTimeField(default=datetime.datetime.now)
        status_code = IntegerField(null=True)
        error_message = TextField(null=True)
        response_time_ms = IntegerField(null=True)
        is_success = BooleanField()
        user_agent = TextField(null=True)
        created_at = DateTimeField(default=datetime.datetime.now)
        
        class Meta:
            database = database
            table_name = 'feed_check_logs'
    
    FeedCheckLog.create_table()
    
    # Create indexes
    database.execute_sql('CREATE INDEX idx_feed_check_logs_feed_id ON feed_check_logs(feed_id)')
    database.execute_sql('CREATE INDEX idx_feed_check_logs_checked_at ON feed_check_logs(checked_at)')
    database.execute_sql('CREATE INDEX idx_feed_check_logs_success ON feed_check_logs(is_success)')

def rollback():
    """Rollback migration"""
    database.execute_sql('DROP TABLE IF EXISTS feed_check_logs')
    
    migrator = SqliteMigrator(database)
    migrate(
        migrator.drop_column('feeds', 'last_checked'),
        migrator.drop_column('feeds', 'accessible'),
        migrator.drop_column('feeds', 'consecutive_failures'),
    )
```

## Query Patterns

### Find Broken Feeds (7+ Days)

```sql
-- Find feeds broken for 7+ days in specific category
SELECT f.*, c.name as category_name
FROM feeds f
LEFT JOIN categories c ON f.category_id = c.id
WHERE f.category_id = ? 
  AND f.accessible = false
  AND (f.last_checked IS NULL OR f.last_checked <= datetime('now', '-7 days'))
ORDER BY f.last_checked ASC;
```

### Get Feed Check History

```sql
-- Get recent check history for a feed
SELECT checked_at, is_success, status_code, error_message, response_time_ms
FROM feed_check_logs
WHERE feed_id = ?
ORDER BY checked_at DESC
LIMIT 10;
```

### Feed Health Summary

```sql
-- Get feed health summary for category
SELECT 
    COUNT(*) as total_feeds,
    SUM(CASE WHEN accessible = true THEN 1 ELSE 0 END) as accessible_feeds,
    SUM(CASE WHEN accessible = false THEN 1 ELSE 0 END) as broken_feeds,
    SUM(CASE WHEN last_checked IS NULL THEN 1 ELSE 0 END) as never_checked
FROM feeds 
WHERE category_id = ?;
```

## Rationale

**Extended Feeds Table**: Adding accessibility tracking directly to the feeds table provides fast access to current status without joins. The consecutive_failures field helps identify feeds that are consistently problematic.

**Separate Logs Table**: Maintaining detailed check history in a separate table prevents feeds table bloat while providing comprehensive audit trail. Foreign key cascade ensures cleanup when feeds are deleted.

**Indexes**: Strategic indexes on feed_id, checked_at, and is_success support the most common query patterns for finding broken feeds and displaying check history.

**Migration Safety**: Using Peewee's migration system ensures safe schema updates in production without manual intervention.

## Performance Considerations

- **Index Usage**: All common queries use indexed columns for fast retrieval
- **Log Retention**: Consider adding log cleanup job to prevent unlimited growth
- **Batch Operations**: Feed checking updates can be batched to reduce database load
- **Connection Pooling**: Existing FastAPI database connection pooling handles concurrent check operations