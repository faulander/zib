# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-23-smart-feed-refresh/spec.md

> Created: 2025-08-23
> Version: 1.0.0

## Schema Changes

### New Fields for Feed Model

Add priority and tracking fields to existing `feeds` table:

```sql
ALTER TABLE feeds ADD COLUMN priority_score REAL DEFAULT 0.0;
ALTER TABLE feeds ADD COLUMN last_post_date DATETIME NULL;
ALTER TABLE feeds ADD COLUMN posting_frequency_days REAL DEFAULT 1.0;
ALTER TABLE feeds ADD COLUMN consecutive_failures INTEGER DEFAULT 0;
ALTER TABLE feeds ADD COLUMN last_successful_refresh DATETIME NULL;
ALTER TABLE feeds ADD COLUMN total_articles_fetched INTEGER DEFAULT 0;
ALTER TABLE feeds ADD COLUMN user_engagement_score REAL DEFAULT 0.0;
```

### New Table: Feed Posting History

Track posting patterns for adaptive scheduling:

```sql
CREATE TABLE feed_posting_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL,
    posting_date DATETIME NOT NULL,
    articles_count INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE
);

CREATE INDEX idx_feed_posting_history_feed_date ON feed_posting_history(feed_id, posting_date);
CREATE INDEX idx_feed_posting_history_date ON feed_posting_history(posting_date);
```

### New Table: Refresh Performance Metrics

Track refresh performance for optimization:

```sql
CREATE TABLE refresh_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    refresh_started_at DATETIME NOT NULL,
    feeds_processed INTEGER NOT NULL DEFAULT 0,
    total_duration_seconds REAL NOT NULL DEFAULT 0.0,
    batch_size INTEGER NOT NULL DEFAULT 10,
    priority_algorithm_version VARCHAR(10) NOT NULL DEFAULT 'v1.0',
    created_at DATETIME NOT NULL
);

CREATE INDEX idx_refresh_metrics_started_at ON refresh_metrics(refresh_started_at);
```

## Migration Implementation

### Migration: Add Feed Priority Fields
```python
def add_feed_priority_fields():
    """Migration to add priority and tracking fields to feeds table"""
    
    migrations = [
        "ALTER TABLE feeds ADD COLUMN priority_score REAL DEFAULT 0.0",
        "ALTER TABLE feeds ADD COLUMN last_post_date DATETIME NULL",
        "ALTER TABLE feeds ADD COLUMN posting_frequency_days REAL DEFAULT 1.0", 
        "ALTER TABLE feeds ADD COLUMN consecutive_failures INTEGER DEFAULT 0",
        "ALTER TABLE feeds ADD COLUMN last_successful_refresh DATETIME NULL",
        "ALTER TABLE feeds ADD COLUMN total_articles_fetched INTEGER DEFAULT 0",
        "ALTER TABLE feeds ADD COLUMN user_engagement_score REAL DEFAULT 0.0"
    ]
    
    for migration in migrations:
        try:
            db.execute_sql(migration)
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                raise
```

## Indexes and Constraints

### Performance Indexes
```sql
CREATE INDEX idx_feeds_priority_score ON feeds(priority_score DESC);
CREATE INDEX idx_feeds_last_successful_refresh ON feeds(last_successful_refresh);
CREATE INDEX idx_feeds_consecutive_failures ON feeds(consecutive_failures);
```

## Rationale

### Priority Score Storage
- **Real numbers** allow fine-grained priority ordering
- **Default 0.0** ensures existing feeds start with neutral priority
- **Indexed** for fast priority-ordered queries

### Posting History Tracking
- **Separate table** prevents feed table bloat with historical data
- **Date-based indexing** enables efficient pattern analysis queries
- **Cascade deletion** maintains data consistency

### Performance Metrics
- **Batch tracking** enables optimization of batch sizes over time  
- **Version tracking** allows A/B testing of priority algorithms
- **Duration tracking** identifies performance bottlenecks