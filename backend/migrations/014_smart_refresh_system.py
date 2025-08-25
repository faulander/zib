#!/usr/bin/env python3
"""
Smart Feed Refresh System Migration
Adds priority scoring, posting history tracking, and refresh metrics tables
"""

from app.core.database import db
from app.core.migrations import Migration
from playhouse.migrate import SqliteMigrator, migrate
from peewee import FloatField, DateTimeField, IntegerField

def up():
    """Apply migration"""
    print("Adding smart refresh system schema...")
    
    migrator = SqliteMigrator(db)
    
    # Add new fields to feeds table for priority tracking
    print("Adding priority and tracking fields to feeds table...")
    
    new_feed_fields = [
        ('priority_score', FloatField(default=0.0)),
        ('last_post_date', DateTimeField(null=True)),
        ('posting_frequency_days', FloatField(default=1.0)),
        ('total_articles_fetched', IntegerField(default=0)),
        ('user_engagement_score', FloatField(default=0.0))
    ]
    
    for field_name, field in new_feed_fields:
        try:
            migrate(
                migrator.add_column('feeds', field_name, field),
            )
            print(f"✓ Added {field_name} column to feeds table")
        except Exception as e:
            if "duplicate column name" in str(e):
                print(f"✓ {field_name} column already exists, skipping")
            else:
                raise
    
    # Create indexes for performance
    print("Creating indexes on feeds table...")
    try:
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_feeds_priority_score ON feeds(priority_score DESC)')
        print("✓ Created priority score index")
    except Exception as e:
        print(f"Warning: Could not create priority score index: {e}")
    
    try:
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_feeds_last_post_date ON feeds(last_post_date)')
        print("✓ Created last post date index")
    except Exception as e:
        print(f"Warning: Could not create last post date index: {e}")
    
    # Create feed_posting_history table
    print("Creating feed_posting_history table...")
    try:
        db.execute_sql('''
            CREATE TABLE IF NOT EXISTS feed_posting_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                posting_date DATETIME NOT NULL,
                articles_count INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE
            )
        ''')
        print("✓ Created feed_posting_history table")
    except Exception as e:
        if "already exists" not in str(e):
            raise
    
    # Create indexes for feed_posting_history
    print("Creating indexes on feed_posting_history table...")
    try:
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_feed_posting_history_feed_date ON feed_posting_history(feed_id, posting_date)')
        print("✓ Created feed-date index on posting history")
    except Exception as e:
        print(f"Warning: Could not create feed-date index: {e}")
    
    try:
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_feed_posting_history_date ON feed_posting_history(posting_date)')
        print("✓ Created date index on posting history")
    except Exception as e:
        print(f"Warning: Could not create date index: {e}")
    
    # Create refresh_metrics table
    print("Creating refresh_metrics table...")
    try:
        db.execute_sql('''
            CREATE TABLE IF NOT EXISTS refresh_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                refresh_started_at DATETIME NOT NULL,
                feeds_processed INTEGER NOT NULL DEFAULT 0,
                total_duration_seconds REAL NOT NULL DEFAULT 0.0,
                batch_size INTEGER NOT NULL DEFAULT 10,
                priority_algorithm_version VARCHAR(10) NOT NULL DEFAULT 'v1.0',
                created_at DATETIME NOT NULL
            )
        ''')
        print("✓ Created refresh_metrics table")
    except Exception as e:
        if "already exists" not in str(e):
            raise
    
    # Create index for refresh_metrics
    try:
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_refresh_metrics_started_at ON refresh_metrics(refresh_started_at)')
        print("✓ Created started_at index on refresh metrics")
    except Exception as e:
        print(f"Warning: Could not create started_at index: {e}")
    
    print("✓ Smart refresh system schema migration completed")

def down():
    """Rollback migration"""
    print("Rolling back smart refresh system schema...")
    
    migrator = SqliteMigrator(db)
    
    # Drop new tables
    try:
        db.execute_sql('DROP TABLE IF EXISTS refresh_metrics')
        print("✓ Dropped refresh_metrics table")
    except Exception as e:
        print(f"Warning: Could not drop refresh_metrics table: {e}")
    
    try:
        db.execute_sql('DROP TABLE IF EXISTS feed_posting_history')
        print("✓ Dropped feed_posting_history table")
    except Exception as e:
        print(f"Warning: Could not drop feed_posting_history table: {e}")
    
    # Remove added columns from feeds table
    field_names = [
        'priority_score',
        'last_post_date', 
        'posting_frequency_days',
        'total_articles_fetched',
        'user_engagement_score'
    ]
    
    for field_name in field_names:
        try:
            migrate(
                migrator.drop_column('feeds', field_name),
            )
            print(f"✓ Removed {field_name} column from feeds table")
        except Exception as e:
            print(f"Warning: Could not remove {field_name} column: {e}")
    
    print("✓ Smart refresh system rollback completed")


class SmartRefreshSystemMigration(Migration):
    '''Smart refresh system migration for priority-based feed processing'''
    
    def up(self):
        '''Apply the migration'''
        up()
    
    def down(self):
        '''Rollback the migration'''
        down()


# Migration instance
migration = SmartRefreshSystemMigration(
    version=14,
    description='Add smart refresh system with priority scoring and metrics tracking'
)