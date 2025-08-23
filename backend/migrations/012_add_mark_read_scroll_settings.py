#!/usr/bin/env python3
"""
Add mark-as-read-on-scroll settings to User model
"""

from app.core.database import db
from app.core.migrations import Migration
from playhouse.migrate import SqliteMigrator, migrate
from peewee import IntegerField

def up():
    """Apply migration"""
    print("Adding mark-as-read-on-scroll settings to users table...")
    
    migrator = SqliteMigrator(db)
    
    # SQLite requires dropping views that reference the table being modified
    # Store the view definition
    user_reading_stats_view = '''CREATE VIEW user_reading_stats AS
            SELECT 
                u.id as user_id,
                u.username,
                COUNT(rs.id) as total_articles,
                COUNT(CASE WHEN rs.is_read = true THEN 1 END) as read_articles,
                COUNT(CASE WHEN rs.is_starred = true THEN 1 END) as starred_articles,
                COUNT(us.id) as subscribed_feeds
            FROM users u
            LEFT JOIN read_statuses rs ON u.id = rs.user_id
            LEFT JOIN user_subscriptions us ON u.id = us.user_id AND us.is_active = true
            GROUP BY u.id, u.username'''
    
    # Drop the view
    try:
        db.execute_sql('DROP VIEW IF EXISTS user_reading_stats')
        print("✓ Dropped user_reading_stats view temporarily")
    except Exception as e:
        print(f"Warning: Could not drop view: {e}")
    
    # Add mark-as-read-on-scroll settings
    try:
        migrate(
            migrator.add_column('users', 'mark_read_scroll_batch_size', IntegerField(default=5)),
        )
        print("✓ Added mark_read_scroll_batch_size column to users table")
    except Exception as e:
        if "duplicate column name" in str(e):
            print("✓ mark_read_scroll_batch_size column already exists, skipping")
        else:
            raise
    
    try:
        migrate(
            migrator.add_column('users', 'mark_read_scroll_delay', IntegerField(default=1000)),
        )
        print("✓ Added mark_read_scroll_delay column to users table")
    except Exception as e:
        if "duplicate column name" in str(e):
            print("✓ mark_read_scroll_delay column already exists, skipping")
        else:
            raise
    
    # Recreate the view
    try:
        db.execute_sql(user_reading_stats_view)
        print("✓ Recreated user_reading_stats view")
    except Exception as e:
        print(f"Warning: Could not recreate view: {e}")
    
    print("✓ Added mark-as-read-on-scroll settings")

def down():
    """Rollback migration"""
    print("Removing mark-as-read-on-scroll settings from users table...")
    
    migrator = SqliteMigrator(db)
    
    # Remove mark-as-read-on-scroll settings
    migrate(
        migrator.drop_column('users', 'mark_read_scroll_batch_size'),
        migrator.drop_column('users', 'mark_read_scroll_delay'),
    )
    
    print("✓ Removed mark-as-read-on-scroll settings")


class MarkReadScrollSettingsMigration(Migration):
    '''Mark-as-read-on-scroll settings migration'''
    
    def up(self):
        '''Apply the migration'''
        up()
    
    def down(self):
        '''Rollback the migration'''
        down()


# Migration instance
migration = MarkReadScrollSettingsMigration(
    version=12,
    description='Add mark-as-read-on-scroll settings to users table'
)