'''
Migration 008: Add show_timestamps_in_list setting to User model

Created: 2025-08-18
'''

import peewee as pw
from app.core.database import db


class ShowTimestampsMigration:
    '''Migration to add show_timestamps_in_list setting'''
    
    def upgrade(self):
        '''Add show_timestamps_in_list column to users table'''
        try:
            db.connect()
            
            # Add show_timestamps_in_list column
            db.execute_sql('''
                ALTER TABLE users 
                ADD COLUMN show_timestamps_in_list BOOLEAN DEFAULT TRUE
            ''')
            
            print('✓ Added show_timestamps_in_list column to users table')
            
        except Exception as e:
            print(f'✗ Migration failed: {e}')
            raise
        finally:
            if not db.is_closed():
                db.close()
    
    def downgrade(self):
        '''Remove show_timestamps_in_list column from users table'''
        try:
            db.connect()
            
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
        finally:
            if not db.is_closed():
                db.close()


# Create migration instance
migration = ShowTimestampsMigration()


if __name__ == '__main__':
    migration.upgrade()