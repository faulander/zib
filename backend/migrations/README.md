# Zib RSS Reader - Database Migrations

This directory contains all database migrations for the Zib RSS Reader project using a robust migration system built on top of Peewee's migration tools.

## Migration System Features

- **Version Tracking**: Uses `schema_version` table to track which migrations have been applied
- **Idempotent Migrations**: All migrations can be run multiple times safely
- **Transaction Safety**: Each migration runs in its own database transaction
- **Rollback Support**: All migrations include rollback functionality
- **Production Ready**: Safe to run in production environments

## Migration Management Commands

### Check Migration Status
```bash
uv run python manage_migrations.py status
```
Shows current database version, available migrations, and pending migrations.

### Apply Pending Migrations
```bash
uv run python manage_migrations.py migrate
```
Applies all pending migrations in order.

### Rollback to Specific Version
```bash
uv run python manage_migrations.py rollback 5
```
Rolls back database to version 5 (removes all migrations above version 5).

### Create New Migration
```bash
uv run python manage_migrations.py create "Add user preferences"
```
Creates a new migration template with the next version number.

## Production Deployment

For production environments, always run migrations before starting the application:

```bash
# Check what will be applied
uv run python manage_migrations.py status

# Apply migrations
uv run python manage_migrations.py migrate

# Start the application
uv run python -m app.main
```

## Development Workflow

During development, the application automatically runs migrations on startup via `run_migrations.py`. This is configured in the main application startup.

## Migration File Structure

Each migration file follows this pattern:

```python
#!/usr/bin/env python3
"""
Description of what this migration does
"""

from app.core.database import db
from app.core.migrations import Migration
from playhouse.migrate import SqliteMigrator, migrate
from peewee import CharField, IntegerField  # Import field types as needed

def up():
    """Apply migration"""
    print("Applying migration: Description")
    
    migrator = SqliteMigrator(db)
    
    # Add your migration logic here
    # For idempotency, handle existing columns/tables:
    try:
        migrate(
            migrator.add_column('table_name', 'new_column', CharField(default=''))
        )
        print("✓ Added new_column to table_name")
    except Exception as e:
        if "duplicate column name" in str(e):
            print("✓ new_column already exists, skipping")
        else:
            raise

def down():
    """Rollback migration"""
    print("Rolling back migration: Description")
    
    migrator = SqliteMigrator(db)
    
    # Add rollback logic here
    migrate(
        migrator.drop_column('table_name', 'new_column')
    )
    print("✓ Removed new_column from table_name")

class MyMigration(Migration):
    """Migration class"""
    
    def up(self):
        up()
    
    def down(self):
        down()

# Migration instance
migration = MyMigration(
    version=12,  # Next available version number
    description="Add user preferences"
)
```

## Best Practices

1. **Always Test Migrations**: Test migrations on a copy of production data before deploying
2. **Make Migrations Idempotent**: Handle cases where columns/tables already exist
3. **Use Transactions**: The system automatically wraps migrations in transactions
4. **Write Rollbacks**: Always implement the `down()` method for rollback capability
5. **Descriptive Names**: Use clear, descriptive migration names and descriptions
6. **Small Changes**: Keep migrations focused on single changes when possible

## Current Database Schema

The database is currently at **version 11** with the following migrations applied:

1. **Migration 1**: Initial database schema with all base tables
2. **Migration 2**: OPML import system tables and import tracking fields  
3. **Migration 3**: Article system with users, articles, subscriptions, and read status
4. **Migration 4**: Add filter system for article filtering
5. **Migration 5**: Increase filter_value column length to support complex queries
6. **Migration 6**: Add user preferences for article display behavior
7. **Migration 7**: Add auto-refresh settings to user preferences
8. **Migration 8**: Add show_timestamps_in_list setting to User model
9. **Migration 9**: Add preferred view mode setting to users table
10. **Migration 10**: Add image_url field to articles table for storing article thumbnails
11. **Migration 11**: Add feed health tracking fields and create feed_check_logs table

## Troubleshooting

### Migration Failed
If a migration fails:
1. Check the error message in the logs
2. Fix the migration file
3. If needed, rollback to a previous version and try again
4. For development, you can manually fix the database and mark the migration as applied

### Column Already Exists Errors
All migrations are designed to handle existing columns gracefully. If you encounter these errors, the migration system will skip the duplicate operation and continue.

### Transaction Errors
If you see "Attempting to close database while transaction is open", ensure your migration doesn't manually manage database connections. Let the migration system handle transactions.

## Files

- `run_migrations.py`: Automatic migration runner for application startup
- `manage_migrations.py`: Manual migration management tool
- `001_*.py` through `011_*.py`: Individual migration files
- `README.md`: This documentation file