# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-25-article-export-plugins/spec.md

> Created: 2025-08-25
> Version: 1.0.0

## Changes

### New Table: export_plugin_configs

This table stores user-specific plugin configurations and enable/disable status.

```sql
CREATE TABLE IF NOT EXISTS export_plugin_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plugin_id VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    config TEXT DEFAULT '{}',  -- JSON string of plugin configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, plugin_id)
);

CREATE INDEX idx_export_plugin_configs_user_plugin 
ON export_plugin_configs(user_id, plugin_id);

CREATE INDEX idx_export_plugin_configs_enabled 
ON export_plugin_configs(user_id, enabled);
```

### New Table: export_logs (Optional - for future analytics)

This table could track export history for analytics purposes (out of current scope but good to plan for).

```sql
CREATE TABLE IF NOT EXISTS export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    article_id INTEGER NOT NULL,
    plugin_id VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);

CREATE INDEX idx_export_logs_user 
ON export_logs(user_id, exported_at DESC);

CREATE INDEX idx_export_logs_article 
ON export_logs(article_id);
```

## Model Implementation

### ExportPluginConfig Model (Peewee)

```python
from peewee import *
import pendulum
import json

class ExportPluginConfig(BaseModel):
    user = ForeignKeyField(User, backref='export_configs', on_delete='CASCADE')
    plugin_id = CharField(max_length=50)
    enabled = BooleanField(default=False)
    config = TextField(default='{}')
    created_at = DateTimeField(default=lambda: pendulum.now('UTC').to_datetime_string())
    updated_at = DateTimeField(default=lambda: pendulum.now('UTC').to_datetime_string())
    
    class Meta:
        database = db
        table_name = 'export_plugin_configs'
        indexes = (
            (('user', 'plugin_id'), True),  # Unique index
        )
    
    def get_config(self):
        """Parse JSON config string to dict"""
        return json.loads(self.config)
    
    def set_config(self, config_dict):
        """Set config from dict"""
        self.config = json.dumps(config_dict)
    
    def save(self, *args, **kwargs):
        self.updated_at = pendulum.now('UTC').to_datetime_string()
        return super().save(*args, **kwargs)
```

### ExportLog Model (Optional - for future use)

```python
class ExportLog(BaseModel):
    user = ForeignKeyField(User, backref='export_logs', on_delete='CASCADE')
    article = ForeignKeyField(Article, backref='export_logs', on_delete='CASCADE')
    plugin_id = CharField(max_length=50)
    success = BooleanField()
    error_message = TextField(null=True)
    exported_at = DateTimeField(default=lambda: pendulum.now('UTC').to_datetime_string())
    
    class Meta:
        database = db
        table_name = 'export_logs'
```

## Migration

### Migration Script

```python
def migrate():
    """Add export plugin configuration tables"""
    with db.atomic():
        # Create export_plugin_configs table
        db.execute_sql("""
            CREATE TABLE IF NOT EXISTS export_plugin_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plugin_id VARCHAR(50) NOT NULL,
                enabled BOOLEAN DEFAULT FALSE,
                config TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, plugin_id)
            )
        """)
        
        # Create indexes
        db.execute_sql("""
            CREATE INDEX IF NOT EXISTS idx_export_plugin_configs_user_plugin 
            ON export_plugin_configs(user_id, plugin_id)
        """)
        
        db.execute_sql("""
            CREATE INDEX IF NOT EXISTS idx_export_plugin_configs_enabled 
            ON export_plugin_configs(user_id, enabled)
        """)
        
        # Optional: Create export_logs table for future use
        db.execute_sql("""
            CREATE TABLE IF NOT EXISTS export_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                article_id INTEGER NOT NULL,
                plugin_id VARCHAR(50) NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            )
        """)
        
        db.execute_sql("""
            CREATE INDEX IF NOT EXISTS idx_export_logs_user 
            ON export_logs(user_id, exported_at DESC)
        """)
        
        db.execute_sql("""
            CREATE INDEX IF NOT EXISTS idx_export_logs_article 
            ON export_logs(article_id)
        """)
```

## Rationale

### Why a separate config table instead of user settings?

1. **Structured data**: Plugin configurations can be complex and having a dedicated table allows for better querying and indexing
2. **Scalability**: Easy to add more plugins without modifying the user settings schema
3. **Performance**: Can query enabled plugins directly without parsing JSON
4. **Future enhancements**: The export_logs table structure allows for future analytics features

### Why JSON for config storage?

1. **Flexibility**: Different plugins have different configuration requirements
2. **Simplicity**: No need for complex EAV (Entity-Attribute-Value) pattern
3. **SQLite support**: SQLite has good JSON support if needed for queries
4. **Schema validation**: Validation happens at the application layer using plugin schemas

### Index Strategy

1. **Unique constraint** on (user_id, plugin_id) ensures one config per plugin per user
2. **Index on enabled** allows quick retrieval of active plugins for a user
3. **Export logs indexes** optimized for common queries (by user, by article)