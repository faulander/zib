# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-22-opml-import-export-improvements/spec.md

> Created: 2025-08-22
> Version: 1.0.0

## Schema Changes

### New Indexes for Performance

**Feed Table Indexes:**
```sql
-- Optimize duplicate detection during import
CREATE INDEX IF NOT EXISTS idx_feed_url ON feed(url);
CREATE INDEX IF NOT EXISTS idx_feed_category_id ON feed(category_id);

-- Optimize export queries
CREATE INDEX IF NOT EXISTS idx_feed_created_at ON feed(created_at);
CREATE INDEX IF NOT EXISTS idx_feed_title ON feed(title);
```

**Category Table Indexes:**
```sql
-- Optimize category duplicate detection
CREATE INDEX IF NOT EXISTS idx_category_name ON category(name);
CREATE INDEX IF NOT EXISTS idx_category_parent_id ON category(parent_id);
```

### Import Job Table Enhancements

**Add Performance Tracking Fields:**
```sql
-- Add performance metrics to existing import_job table
ALTER TABLE import_job ADD COLUMN feeds_per_second REAL DEFAULT 0.0;
ALTER TABLE import_job ADD COLUMN estimated_completion_at DATETIME;
ALTER TABLE import_job ADD COLUMN concurrent_limit INTEGER DEFAULT 10;
ALTER TABLE import_job ADD COLUMN batch_size INTEGER DEFAULT 50;
ALTER TABLE import_job ADD COLUMN current_item_name TEXT;
ALTER TABLE import_job ADD COLUMN validation_errors_json TEXT; -- JSON array of validation errors
```

**Migration Script:**
```sql
-- Migration: Add performance fields to import_job table
-- File: migrations/003_import_performance_fields.py

def upgrade():
    # Add new performance tracking fields
    migrator.add_column('import_job', 'feeds_per_second', pw.FloatField(default=0.0))
    migrator.add_column('import_job', 'estimated_completion_at', pw.DateTimeField(null=True))
    migrator.add_column('import_job', 'concurrent_limit', pw.IntegerField(default=10))
    migrator.add_column('import_job', 'batch_size', pw.IntegerField(default=50))
    migrator.add_column('import_job', 'current_item_name', pw.TextField(null=True))
    migrator.add_column('import_job', 'validation_errors_json', pw.TextField(null=True))

def downgrade():
    # Remove performance tracking fields
    migrator.drop_column('import_job', 'validation_errors_json')
    migrator.drop_column('import_job', 'current_item_name')
    migrator.drop_column('import_job', 'batch_size')
    migrator.drop_column('import_job', 'concurrent_limit')
    migrator.drop_column('import_job', 'estimated_completion_at')
    migrator.drop_column('import_job', 'feeds_per_second')
```

### Export Configuration Table (Optional)

**New Table for Export Preferences:**
```sql
-- Optional: Store user export preferences
CREATE TABLE IF NOT EXISTS export_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    default_format TEXT DEFAULT 'opml',
    include_categories TEXT, -- JSON array of category IDs
    exclude_categories TEXT, -- JSON array of category IDs  
    auto_timestamp_filename BOOLEAN DEFAULT true,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_export_config_user_id ON export_config(user_id);
```

## Performance Optimizations

### Database Connection Configuration

**SQLite Optimization Settings:**
```sql
-- Apply these PRAGMA settings for better performance during imports
PRAGMA journal_mode = WAL;           -- Write-Ahead Logging for better concurrency
PRAGMA synchronous = NORMAL;         -- Balance durability vs performance  
PRAGMA cache_size = -64000;          -- 64MB cache size
PRAGMA temp_store = MEMORY;          -- Store temporary data in memory
PRAGMA mmap_size = 268435456;        -- 256MB memory-mapped I/O
```

### Batch Operation Queries

**Batch Feed Insertion:**
```sql
-- Prepared statement for batch feed insertion
INSERT INTO feed (title, url, site_url, description, category_id, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?);

-- Use with executemany() for batch operations:
-- cursor.executemany(query, feed_data_list)
```

**Batch Category Creation:**
```sql
-- Prepared statement for batch category creation  
INSERT INTO category (name, description, parent_id, created_at, updated_at)
VALUES (?, ?, ?, ?, ?);
```

### Optimized Duplicate Detection Queries

**Feed Duplicate Check:**
```sql
-- Single query to get all existing feed URLs for duplicate detection
SELECT url FROM feed WHERE url IN (?, ?, ?, ...);

-- More efficient than individual EXISTS queries
```

**Category Duplicate Check:**
```sql
-- Single query to get all existing category names
SELECT name FROM category WHERE name IN (?, ?, ?, ...);
```

## Export Query Optimizations

### Hierarchical Category Export

**Category with Feed Count:**
```sql
-- Get categories with feed counts for export options
SELECT 
    c.id,
    c.name,
    c.description,
    c.parent_id,
    COUNT(f.id) as feed_count
FROM category c
LEFT JOIN feed f ON c.id = f.category_id
GROUP BY c.id, c.name, c.description, c.parent_id
ORDER BY c.name;
```

**Feeds by Category for Export:**
```sql
-- Get all feeds organized by category for OPML export
SELECT 
    f.id,
    f.title,
    f.url,
    f.site_url,
    f.description,
    c.name as category_name,
    c.id as category_id
FROM feed f
LEFT JOIN category c ON f.category_id = c.id
WHERE (? IS NULL OR c.id IN (?))  -- Optional category filtering
ORDER BY c.name, f.title;
```

## Data Integrity

### Foreign Key Constraints

**Ensure Referential Integrity:**
```sql
-- Enable foreign key constraints for data consistency
PRAGMA foreign_keys = ON;

-- Verify feed-category relationships during import
ALTER TABLE feed ADD CONSTRAINT fk_feed_category
    FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE SET NULL;
```

### Transaction Management

**Import Transaction Pattern:**
```sql
-- Wrap import operations in transactions for consistency
BEGIN TRANSACTION;

-- Batch insert categories
INSERT INTO category (...) VALUES (...);

-- Batch insert feeds with category references
INSERT INTO feed (...) VALUES (...);

-- Update import job status
UPDATE import_job SET status = 'completed' WHERE id = ?;

COMMIT;
-- ROLLBACK on any errors
```

## Backup Considerations

### Pre-Import Backup

**Automatic Backup Before Large Imports:**
```sql
-- Create backup table before major imports
CREATE TABLE feed_backup_20250822 AS SELECT * FROM feed;
CREATE TABLE category_backup_20250822 AS SELECT * FROM category;

-- Drop backup tables after successful import confirmation
```

### Export Data Validation

**Data Consistency Checks:**
```sql
-- Verify export data integrity
SELECT 
    COUNT(*) as total_feeds,
    COUNT(DISTINCT category_id) as categories_used,
    COUNT(CASE WHEN category_id IS NULL THEN 1 END) as uncategorized_feeds
FROM feed;

-- Check for orphaned feeds (invalid category_id)
SELECT COUNT(*) FROM feed f 
LEFT JOIN category c ON f.category_id = c.id 
WHERE f.category_id IS NOT NULL AND c.id IS NULL;
```

## Migration Rollback Plan

**Rollback Strategy:**
```sql
-- If migration fails, rollback schema changes
ALTER TABLE import_job DROP COLUMN validation_errors_json;
ALTER TABLE import_job DROP COLUMN current_item_name;
ALTER TABLE import_job DROP COLUMN batch_size;
ALTER TABLE import_job DROP COLUMN concurrent_limit;
ALTER TABLE import_job DROP COLUMN estimated_completion_at;
ALTER TABLE import_job DROP COLUMN feeds_per_second;

-- Remove new indexes
DROP INDEX IF EXISTS idx_feed_url;
DROP INDEX IF EXISTS idx_feed_category_id;
DROP INDEX IF EXISTS idx_category_name;
```

## Performance Monitoring

**Query Performance Tracking:**
```sql
-- Enable query analysis for performance monitoring
PRAGMA compile_options;
EXPLAIN QUERY PLAN SELECT * FROM feed WHERE url = ?;
EXPLAIN QUERY PLAN SELECT * FROM category WHERE name = ?;

-- Monitor index usage
PRAGMA index_info('idx_feed_url');
PRAGMA index_list('feed');
```

The database schema changes focus on performance optimization through proper indexing and efficient batch operations while maintaining data integrity and providing rollback capabilities.