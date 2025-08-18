'''Add user preferences for article display behavior'''

from app.core.database import db
from peewee import OperationalError
import logging

logger = logging.getLogger(__name__)

class UserArticleDisplayPreferencesMigration:
    version = 6
    description = 'Add user preferences for article display behavior'
    
    def up(self):
        '''Apply migration - add new columns to users table'''
        try:
            with db.atomic():
                # Add new columns to users table
                db.execute_sql('''
                    ALTER TABLE users ADD COLUMN open_webpage_for_short_articles BOOLEAN DEFAULT 0
                ''')
                
                db.execute_sql('''
                    ALTER TABLE users ADD COLUMN short_article_threshold INTEGER DEFAULT 500
                ''')
                
                logger.info('Added article display preference columns to users table')
                return True
                
        except OperationalError as e:
            logger.error(f'Failed to add article display preferences: {e}')
            return False
        except Exception as e:
            logger.error(f'Unexpected error in article display preferences migration: {e}')
            return False
    
    def down(self):
        '''Rollback migration - remove columns from users table'''
        try:
            with db.atomic():
                # SQLite doesn't support DROP COLUMN, so we need to recreate the table
                db.execute_sql('''
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(50) NOT NULL UNIQUE,
                        email VARCHAR(254) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        feeds_per_page INTEGER NOT NULL DEFAULT 50,
                        default_view VARCHAR(20) NOT NULL DEFAULT 'unread',
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        last_login TIMESTAMP
                    )
                ''')
                
                # Copy data from old table (excluding new columns)
                db.execute_sql('''
                    INSERT INTO users_new (
                        id, username, email, password_hash, is_active, feeds_per_page, 
                        default_view, created_at, updated_at, last_login
                    )
                    SELECT 
                        id, username, email, password_hash, is_active, feeds_per_page, 
                        default_view, created_at, updated_at, last_login
                    FROM users
                ''')
                
                # Drop old table and rename new one
                db.execute_sql('DROP TABLE users')
                db.execute_sql('ALTER TABLE users_new RENAME TO users')
                
                # Recreate indexes
                db.execute_sql('CREATE UNIQUE INDEX idx_users_username ON users(username)')
                db.execute_sql('CREATE UNIQUE INDEX idx_users_email ON users(email)')
                db.execute_sql('CREATE INDEX idx_users_is_active ON users(is_active)')
                
                logger.info('Removed article display preference columns from users table')
                return True
                
        except Exception as e:
            logger.error(f'Failed to rollback article display preferences migration: {e}')
            return False


# Create module-level migration instance
migration = UserArticleDisplayPreferencesMigration()