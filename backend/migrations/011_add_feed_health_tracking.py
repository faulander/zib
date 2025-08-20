#!/usr/bin/env python3
"""
Add feed health tracking fields and create feed_check_logs table
"""

from app.core.database import db
from app.core.migrations import Migration
from playhouse.migrate import SqliteMigrator, migrate
from datetime import datetime
from peewee import DateTimeField, BooleanField, IntegerField

def up():
    """Apply migration"""
    print("Adding feed health tracking fields and feed_check_logs table...")
    
    migrator = SqliteMigrator(db)
    
    # Add health tracking fields to feeds table (skip existing columns)
    try:
        migrate(
            migrator.add_column('feeds', 'last_checked', DateTimeField(null=True)),
        )
        print("✓ Added last_checked column to feeds table")
    except Exception as e:
        if "duplicate column name" in str(e):
            print("✓ last_checked column already exists, skipping")
        else:
            raise
            
    try:
        migrate(
            migrator.add_column('feeds', 'accessible', BooleanField(default=True)),
        )
        print("✓ Added accessible column to feeds table")
    except Exception as e:
        if "duplicate column name" in str(e):
            print("✓ accessible column already exists, skipping")
        else:
            raise
            
    try:
        migrate(
            migrator.add_column('feeds', 'consecutive_failures', IntegerField(default=0)),
        )
        print("✓ Added consecutive_failures column to feeds table")
    except Exception as e:
        if "duplicate column name" in str(e):
            print("✓ consecutive_failures column already exists, skipping")
        else:
            raise
    
    # Create feed_check_logs table
    try:
        db.execute_sql('''
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
            )
        ''')
        print("✓ Created feed_check_logs table")
    except Exception as e:
        if "already exists" in str(e):
            print("✓ feed_check_logs table already exists, skipping")
        else:
            raise
    
    # Create indexes for performance
    indexes = [
        ('idx_feed_check_logs_feed_id', 'CREATE INDEX IF NOT EXISTS idx_feed_check_logs_feed_id ON feed_check_logs(feed_id)'),
        ('idx_feed_check_logs_checked_at', 'CREATE INDEX IF NOT EXISTS idx_feed_check_logs_checked_at ON feed_check_logs(checked_at)'),
        ('idx_feed_check_logs_success', 'CREATE INDEX IF NOT EXISTS idx_feed_check_logs_success ON feed_check_logs(is_success)'),
        ('idx_feed_check_logs_feed_checked_at', 'CREATE INDEX IF NOT EXISTS idx_feed_check_logs_feed_checked_at ON feed_check_logs(feed_id, checked_at)')
    ]
    
    for index_name, sql in indexes:
        try:
            db.execute_sql(sql)
            print(f"✓ Created index {index_name}")
        except Exception as e:
            print(f"✓ Index {index_name} already exists or skipped")
    
    print("✓ Added feed health tracking fields")
    print("✓ Created feed_check_logs table with indexes")

def down():
    """Rollback migration"""
    print("Removing feed health tracking fields and feed_check_logs table...")
    
    migrator = SqliteMigrator(db)
    
    # Drop feed_check_logs table (will also drop indexes)
    db.execute_sql('DROP TABLE IF EXISTS feed_check_logs')
    
    # Remove health tracking fields from feeds table
    migrate(
        migrator.drop_column('feeds', 'last_checked'),
        migrator.drop_column('feeds', 'accessible'),
        migrator.drop_column('feeds', 'consecutive_failures'),
    )
    
    print("✓ Dropped feed_check_logs table")
    print("✓ Removed feed health tracking fields")


class FeedHealthTrackingMigration(Migration):
    '''Feed health tracking migration'''
    
    def up(self):
        '''Apply the migration'''
        up()
    
    def down(self):
        '''Rollback the migration'''
        down()


# Migration instance
migration = FeedHealthTrackingMigration(
    version=11,
    description='Add feed health tracking fields and create feed_check_logs table'
)