#!/usr/bin/env python3
"""
Add font scale setting for accessibility to User model
"""

from app.core.database import db
from app.core.migrations import Migration
from playhouse.migrate import SqliteMigrator, migrate
from peewee import FloatField

def up():
    """Apply migration"""
    print("Adding font scale setting to users table...")
    
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
    
    # Add font scale setting
    try:
        migrate(
            migrator.add_column('users', 'font_scale', FloatField(default=1.0)),
        )
        print("✓ Added font_scale column to users table")
    except Exception as e:
        if "duplicate column name" in str(e):
            print("✓ font_scale column already exists, skipping")
        else:
            raise
    
    # Recreate the view
    try:
        db.execute_sql(user_reading_stats_view)
        print("✓ Recreated user_reading_stats view")
    except Exception as e:
        print(f"Warning: Could not recreate view: {e}")
    
    print("✓ Added font scale setting for accessibility")

def down():
    """Rollback migration"""
    print("Removing font scale setting from users table...")
    
    migrator = SqliteMigrator(db)
    
    # Remove font scale setting
    migrate(
        migrator.drop_column('users', 'font_scale'),
    )
    
    print("✓ Removed font scale setting")


class FontScaleSettingMigration(Migration):
    '''Font scale setting migration for accessibility'''
    
    def up(self):
        '''Apply the migration'''
        up()
    
    def down(self):
        '''Rollback the migration'''
        down()


# Migration instance
migration = FontScaleSettingMigration(
    version=13,
    description='Add font scale setting for accessibility to users table'
)