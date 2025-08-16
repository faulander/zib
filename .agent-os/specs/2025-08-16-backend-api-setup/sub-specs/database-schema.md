# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-16-backend-api-setup/spec.md

> Created: 2025-08-16
> Version: 1.0.0

## Schema Changes

### New Tables

#### feeds
```sql
CREATE TABLE feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    description TEXT,
    category_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    fetch_interval INTEGER DEFAULT 3600,
    last_fetched DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
);
```

#### categories
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    color TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### filters
```sql
CREATE TABLE filters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    criteria TEXT NOT NULL, -- JSON stored as TEXT
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### schema_version
```sql
CREATE TABLE schema_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL UNIQUE,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
```

### Indexes

```sql
-- Unique indexes for data integrity
CREATE UNIQUE INDEX idx_feeds_url ON feeds(url);
CREATE UNIQUE INDEX idx_categories_name ON categories(name);

-- Performance indexes
CREATE INDEX idx_feeds_category_id ON feeds(category_id);
CREATE INDEX idx_feeds_is_active ON feeds(is_active);
CREATE INDEX idx_feeds_last_fetched ON feeds(last_fetched);
CREATE INDEX idx_filters_type ON filters(type);
CREATE INDEX idx_filters_is_active ON filters(is_active);
```

### Triggers for Updated Timestamps

```sql
-- Update timestamp trigger for feeds
CREATE TRIGGER update_feeds_timestamp 
AFTER UPDATE ON feeds
BEGIN
    UPDATE feeds SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamp trigger for categories
CREATE TRIGGER update_categories_timestamp 
AFTER UPDATE ON categories
BEGIN
    UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamp trigger for filters
CREATE TRIGGER update_filters_timestamp 
AFTER UPDATE ON filters
BEGIN
    UPDATE filters SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

## Migrations

### Migration System Design

The migration system will use a simple version-based approach:

1. Each migration has a sequential version number
2. Migrations are stored in `migrations/` directory
3. Current schema version is tracked in `schema_version` table
4. Migrations run in order from current version to target version

### Migration File Structure

```
migrations/
├── 001_initial_schema.py
├── 002_add_indexes.py
└── 003_add_triggers.py
```

### Migration 001: Initial Schema

```python
# migrations/001_initial_schema.py

def up():
    """Create initial database schema"""
    return [
        """
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            color TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT,
            description TEXT,
            category_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            fetch_interval INTEGER DEFAULT 3600,
            last_fetched DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
        )
        """,
        """
        CREATE TABLE filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            criteria TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE schema_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL UNIQUE,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
        """,
        """
        INSERT INTO schema_version (version, description) 
        VALUES (1, 'Initial schema creation')
        """
    ]

def down():
    """Rollback initial schema"""
    return [
        "DROP TABLE IF EXISTS filters",
        "DROP TABLE IF EXISTS feeds", 
        "DROP TABLE IF EXISTS categories",
        "DROP TABLE IF EXISTS schema_version"
    ]
```

### Migration 002: Add Indexes

```python
# migrations/002_add_indexes.py

def up():
    """Add performance and integrity indexes"""
    return [
        "CREATE UNIQUE INDEX idx_feeds_url ON feeds(url)",
        "CREATE UNIQUE INDEX idx_categories_name ON categories(name)",
        "CREATE INDEX idx_feeds_category_id ON feeds(category_id)",
        "CREATE INDEX idx_feeds_is_active ON feeds(is_active)",
        "CREATE INDEX idx_feeds_last_fetched ON feeds(last_fetched)",
        "CREATE INDEX idx_filters_type ON filters(type)",
        "CREATE INDEX idx_filters_is_active ON filters(is_active)",
        """
        INSERT INTO schema_version (version, description) 
        VALUES (2, 'Add database indexes')
        """
    ]

def down():
    """Remove indexes"""
    return [
        "DROP INDEX IF EXISTS idx_feeds_url",
        "DROP INDEX IF EXISTS idx_categories_name", 
        "DROP INDEX IF EXISTS idx_feeds_category_id",
        "DROP INDEX IF EXISTS idx_feeds_is_active",
        "DROP INDEX IF EXISTS idx_feeds_last_fetched",
        "DROP INDEX IF EXISTS idx_filters_type",
        "DROP INDEX IF EXISTS idx_filters_is_active",
        "DELETE FROM schema_version WHERE version = 2"
    ]
```

### Migration 003: Add Triggers

```python
# migrations/003_add_triggers.py

def up():
    """Add automatic timestamp update triggers"""
    return [
        """
        CREATE TRIGGER update_feeds_timestamp 
        AFTER UPDATE ON feeds
        BEGIN
            UPDATE feeds SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """,
        """
        CREATE TRIGGER update_categories_timestamp 
        AFTER UPDATE ON categories
        BEGIN
            UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """,
        """
        CREATE TRIGGER update_filters_timestamp 
        AFTER UPDATE ON filters
        BEGIN
            UPDATE filters SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """,
        """
        INSERT INTO schema_version (version, description) 
        VALUES (3, 'Add timestamp update triggers')
        """
    ]

def down():
    """Remove triggers"""
    return [
        "DROP TRIGGER IF EXISTS update_feeds_timestamp",
        "DROP TRIGGER IF EXISTS update_categories_timestamp",
        "DROP TRIGGER IF EXISTS update_filters_timestamp",
        "DELETE FROM schema_version WHERE version = 3"
    ]
```

## Data Validation Rules

### Feed Validation
- URL must be valid HTTP/HTTPS URL
- URL must be unique across all feeds
- Title limited to 255 characters
- fetch_interval must be positive integer (minimum 300 seconds)

### Category Validation  
- Name must be unique and non-empty
- Name limited to 100 characters
- Color must be valid hex color code (if provided)

### Filter Validation
- Name must be non-empty, limited to 100 characters
- Type must be from predefined list: ['keyword', 'category', 'author', 'date_range']
- Criteria must be valid JSON matching type schema