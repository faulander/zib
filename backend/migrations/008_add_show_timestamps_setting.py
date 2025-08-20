'''
Migration 008: Add show_timestamps_in_list setting to User model

Created: 2025-08-18
'''

import peewee as pw
from app.core.database import db
from app.core.migrations import Migration


class ShowTimestampsMigration(Migration):
    '''Migration to add show_timestamps_in_list setting'''
    
    def up(self):
        '''Add show_timestamps_in_list column to users table'''
        try:
            # Add show_timestamps_in_list column (skip if already exists)
            db.execute_sql('''
                ALTER TABLE users 
                ADD COLUMN show_timestamps_in_list BOOLEAN DEFAULT TRUE
            ''')
            
            print('✓ Added show_timestamps_in_list column to users table')
            
        except Exception as e:
            if "duplicate column name" in str(e):
                print('✓ show_timestamps_in_list column already exists, skipping')
            else:
                print(f'✗ Migration failed: {e}')
                raise
    
    def down(self):
        '''Remove show_timestamps_in_list column from users table'''
        try:
            # Remove show_timestamps_in_list column
            # SQLite doesn't support DROP COLUMN, so we need to recreate table
            db.execute_sql('''
                CREATE TABLE users_backup AS 
                SELECT id, username, email, password_hash, is_active, feeds_per_page, 
                       default_view, open_webpage_for_short_articles, short_article_threshold,
                       auto_refresh_feeds, auto_refresh_interval_minutes,
                       created_at, updated_at, last_login
                FROM users
            ''')
            
            db.execute_sql('DROP TABLE users')
            db.execute_sql('ALTER TABLE users_backup RENAME TO users')
            
            print('✓ Removed show_timestamps_in_list column from users table')
            
        except Exception as e:
            print(f'✗ Rollback failed: {e}')
            raise


# Create migration instance
migration = ShowTimestampsMigration(
    version=8,
    description='Add show_timestamps_in_list setting to User model'
)


if __name__ == '__main__':
    migration.up()