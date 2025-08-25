# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-16-opml-import-feature/spec.md

> Created: 2025-08-16
> Version: 1.0.0

## Schema Changes

### New Tables

#### import_jobs
Tracks OPML import job status and metadata

```sql
CREATE TABLE import_jobs (
  id TEXT PRIMARY KEY,  -- Format: 'imp_' + random string
  user_id INTEGER NOT NULL,
  filename TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed, cancelled
  duplicate_strategy TEXT NOT NULL DEFAULT 'skip',  -- skip, update, merge, prompt
  category_parent_id INTEGER,
  validate_feeds BOOLEAN NOT NULL DEFAULT true,
  
  -- Progress tracking
  total_steps INTEGER DEFAULT 0,
  current_step INTEGER DEFAULT 0,
  current_phase TEXT,  -- parsing, creating_categories, validating_feeds, importing_feeds
  
  -- Results summary
  categories_created INTEGER DEFAULT 0,
  feeds_imported INTEGER DEFAULT 0,
  feeds_failed INTEGER DEFAULT 0,
  duplicates_found INTEGER DEFAULT 0,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  
  -- Error information
  error_message TEXT,
  error_details TEXT,
  
  FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  FOREIGN KEY (category_parent_id) REFERENCES categories (id) ON DELETE SET NULL
);
```

#### import_results
Detailed results for each imported item

```sql
CREATE TABLE import_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  import_job_id TEXT NOT NULL,
  item_type TEXT NOT NULL,  -- category, feed
  item_name TEXT NOT NULL,
  item_url TEXT,  -- NULL for categories
  status TEXT NOT NULL,  -- success, failed, duplicate_skipped, duplicate_updated, duplicate_merged
  error_message TEXT,
  error_code TEXT,
  
  -- References to created items
  created_category_id INTEGER,
  created_feed_id INTEGER,
  existing_item_id INTEGER,  -- For duplicate handling
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (import_job_id) REFERENCES import_jobs (id) ON DELETE CASCADE,
  FOREIGN KEY (created_category_id) REFERENCES categories (id) ON DELETE SET NULL,
  FOREIGN KEY (created_feed_id) REFERENCES feeds (id) ON DELETE SET NULL
);
```

#### import_feed_validation
Cache feed validation results to avoid duplicate requests

```sql
CREATE TABLE import_feed_validation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  feed_url TEXT NOT NULL UNIQUE,
  is_valid BOOLEAN NOT NULL,
  final_url TEXT,  -- After redirects
  title TEXT,
  description TEXT,
  feed_type TEXT,  -- rss, atom, unknown
  error_message TEXT,
  error_code TEXT,
  validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP  -- Cache expiration
);
```

### Table Modifications

#### categories
Add support for tracking import source

```sql
-- Add column to track import source
ALTER TABLE categories ADD COLUMN import_job_id TEXT;
ALTER TABLE categories ADD FOREIGN KEY (import_job_id) REFERENCES import_jobs (id) ON DELETE SET NULL;
```

#### feeds
Add support for tracking import source and OPML metadata

```sql
-- Add columns to track import source and preserve OPML metadata
ALTER TABLE feeds ADD COLUMN import_job_id TEXT;
ALTER TABLE feeds ADD COLUMN opml_title TEXT;  -- Original title from OPML
ALTER TABLE feeds ADD COLUMN opml_description TEXT;  -- Original description from OPML
ALTER TABLE feeds ADD COLUMN opml_html_url TEXT;  -- HTML URL from OPML

ALTER TABLE feeds ADD FOREIGN KEY (import_job_id) REFERENCES import_jobs (id) ON DELETE SET NULL;
```

## Indexes

### Performance Indexes

```sql
-- Import job lookups
CREATE INDEX idx_import_jobs_user_id ON import_jobs (user_id);
CREATE INDEX idx_import_jobs_status ON import_jobs (status);
CREATE INDEX idx_import_jobs_created_at ON import_jobs (created_at);

-- Import results lookups
CREATE INDEX idx_import_results_job_id ON import_results (import_job_id);
CREATE INDEX idx_import_results_status ON import_results (status);
CREATE INDEX idx_import_results_item_type ON import_results (item_type);

-- Feed validation cache
CREATE INDEX idx_import_feed_validation_url ON import_feed_validation (feed_url);
CREATE INDEX idx_import_feed_validation_expires ON import_feed_validation (expires_at);

-- Track items by import source
CREATE INDEX idx_categories_import_job ON categories (import_job_id);
CREATE INDEX idx_feeds_import_job ON feeds (import_job_id);
```

### Unique Constraints

```sql
-- Prevent duplicate import results for same job and item
CREATE UNIQUE INDEX idx_import_results_unique ON import_results (import_job_id, item_type, item_name, item_url);
```

## Migrations

### Migration 001: Create Import System Tables

```python
def upgrade():
    # Create import_jobs table
    db.execute_sql('''
        CREATE TABLE import_jobs (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            duplicate_strategy TEXT NOT NULL DEFAULT 'skip',
            category_parent_id INTEGER,
            validate_feeds BOOLEAN NOT NULL DEFAULT true,
            total_steps INTEGER DEFAULT 0,
            current_step INTEGER DEFAULT 0,
            current_phase TEXT,
            categories_created INTEGER DEFAULT 0,
            feeds_imported INTEGER DEFAULT 0,
            feeds_failed INTEGER DEFAULT 0,
            duplicates_found INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            error_details TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (category_parent_id) REFERENCES categories (id) ON DELETE SET NULL
        )
    ''')
    
    # Create import_results table
    db.execute_sql('''
        CREATE TABLE import_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_job_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            item_url TEXT,
            status TEXT NOT NULL,
            error_message TEXT,
            error_code TEXT,
            created_category_id INTEGER,
            created_feed_id INTEGER,
            existing_item_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (import_job_id) REFERENCES import_jobs (id) ON DELETE CASCADE,
            FOREIGN KEY (created_category_id) REFERENCES categories (id) ON DELETE SET NULL,
            FOREIGN KEY (created_feed_id) REFERENCES feeds (id) ON DELETE SET NULL
        )
    ''')
    
    # Create import_feed_validation table
    db.execute_sql('''
        CREATE TABLE import_feed_validation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_url TEXT NOT NULL UNIQUE,
            is_valid BOOLEAN NOT NULL,
            final_url TEXT,
            title TEXT,
            description TEXT,
            feed_type TEXT,
            error_message TEXT,
            error_code TEXT,
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')
    
    # Create indexes
    db.execute_sql('CREATE INDEX idx_import_jobs_user_id ON import_jobs (user_id)')
    db.execute_sql('CREATE INDEX idx_import_jobs_status ON import_jobs (status)')
    db.execute_sql('CREATE INDEX idx_import_jobs_created_at ON import_jobs (created_at)')
    db.execute_sql('CREATE INDEX idx_import_results_job_id ON import_results (import_job_id)')
    db.execute_sql('CREATE INDEX idx_import_results_status ON import_results (status)')
    db.execute_sql('CREATE INDEX idx_import_results_item_type ON import_results (item_type)')
    db.execute_sql('CREATE INDEX idx_import_feed_validation_url ON import_feed_validation (feed_url)')
    db.execute_sql('CREATE INDEX idx_import_feed_validation_expires ON import_feed_validation (expires_at)')

def downgrade():
    db.execute_sql('DROP INDEX IF EXISTS idx_import_feed_validation_expires')
    db.execute_sql('DROP INDEX IF EXISTS idx_import_feed_validation_url')
    db.execute_sql('DROP INDEX IF EXISTS idx_import_results_item_type')
    db.execute_sql('DROP INDEX IF EXISTS idx_import_results_status')
    db.execute_sql('DROP INDEX IF EXISTS idx_import_results_job_id')
    db.execute_sql('DROP INDEX IF EXISTS idx_import_jobs_created_at')
    db.execute_sql('DROP INDEX IF EXISTS idx_import_jobs_status')
    db.execute_sql('DROP INDEX IF EXISTS idx_import_jobs_user_id')
    db.execute_sql('DROP TABLE IF EXISTS import_feed_validation')
    db.execute_sql('DROP TABLE IF EXISTS import_results')
    db.execute_sql('DROP TABLE IF EXISTS import_jobs')
```

### Migration 002: Add Import Tracking to Existing Tables

```python
def upgrade():
    # Add import tracking to categories
    db.execute_sql('ALTER TABLE categories ADD COLUMN import_job_id TEXT')
    db.execute_sql('CREATE INDEX idx_categories_import_job ON categories (import_job_id)')
    
    # Add import tracking and OPML metadata to feeds
    db.execute_sql('ALTER TABLE feeds ADD COLUMN import_job_id TEXT')
    db.execute_sql('ALTER TABLE feeds ADD COLUMN opml_title TEXT')
    db.execute_sql('ALTER TABLE feeds ADD COLUMN opml_description TEXT')
    db.execute_sql('ALTER TABLE feeds ADD COLUMN opml_html_url TEXT')
    db.execute_sql('CREATE INDEX idx_feeds_import_job ON feeds (import_job_id)')

def downgrade():
    # Remove indexes
    db.execute_sql('DROP INDEX IF EXISTS idx_feeds_import_job')
    db.execute_sql('DROP INDEX IF EXISTS idx_categories_import_job')
    
    # Remove columns (SQLite doesn't support DROP COLUMN, would need table recreation)
    # For development, this would require recreating tables without these columns
```

## Data Integrity Constraints

### Import Job Lifecycle
- Import jobs must have valid status transitions: pending → processing → (completed|failed|cancelled)
- Import jobs cannot be modified once in 'completed', 'failed', or 'cancelled' status
- Import jobs older than 24 hours should be eligible for cleanup

### Import Results Consistency
- Import results must reference a valid import job
- Success status results should have either created_category_id or created_feed_id
- Failed status results should have error_message and error_code
- Duplicate status results should have existing_item_id

### Feed Validation Cache
- Validation cache entries should have expires_at set to 1 hour after validated_at
- Expired validation cache entries should be cleaned up automatically
- Validation cache should be cleared when feed URLs are normalized