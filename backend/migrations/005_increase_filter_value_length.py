'''Increase filter_value column length to support complex queries'''

from app.core.database import db
from peewee import OperationalError
import logging

logger = logging.getLogger(__name__)

class IncreaseFilterValueLengthMigration:
    version = 5
    description = 'Increase filter_value column length to support complex queries'
    
    def up(self):
        '''Apply migration - increase filter_value length'''
        try:
            with db.atomic():
                # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
                db.execute_sql('''
                    CREATE TABLE filter_rules_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        filter_type VARCHAR(20) NOT NULL DEFAULT 'title_contains',
                        filter_value VARCHAR(2000) NOT NULL,
                        category_id INTEGER,
                        feed_id INTEGER,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        case_sensitive BOOLEAN NOT NULL DEFAULT 0,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
                    )
                ''')
                
                # Copy data from old table
                db.execute_sql('''
                    INSERT INTO filter_rules_new 
                    SELECT * FROM filter_rules
                ''')
                
                # Drop old table and rename new one
                db.execute_sql('DROP TABLE filter_rules')
                db.execute_sql('ALTER TABLE filter_rules_new RENAME TO filter_rules')
                
                # Recreate indexes
                db.execute_sql('CREATE INDEX idx_filter_rules_user_active ON filter_rules(user_id, is_active)')
                db.execute_sql('CREATE INDEX idx_filter_rules_user_category ON filter_rules(user_id, category_id)')
                db.execute_sql('CREATE INDEX idx_filter_rules_created_at ON filter_rules(created_at)')
                
                logger.info('Increased filter_value column length to 2000 characters')
                return True
                
        except OperationalError as e:
            logger.error(f'Failed to increase filter_value length: {e}')
            return False
        except Exception as e:
            logger.error(f'Unexpected error in filter length migration: {e}')
            return False
    
    def down(self):
        '''Rollback migration - decrease filter_value length'''
        try:
            with db.atomic():
                # SQLite recreation with original length
                db.execute_sql('''
                    CREATE TABLE filter_rules_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        filter_type VARCHAR(20) NOT NULL DEFAULT 'title_contains',
                        filter_value VARCHAR(500) NOT NULL,
                        category_id INTEGER,
                        feed_id INTEGER,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        case_sensitive BOOLEAN NOT NULL DEFAULT 0,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
                    )
                ''')
                
                # Copy data (this might fail if there are values > 500 chars)
                db.execute_sql('''
                    INSERT INTO filter_rules_new 
                    SELECT * FROM filter_rules 
                    WHERE LENGTH(filter_value) <= 500
                ''')
                
                # Drop old table and rename new one
                db.execute_sql('DROP TABLE filter_rules')
                db.execute_sql('ALTER TABLE filter_rules_new RENAME TO filter_rules')
                
                # Recreate indexes
                db.execute_sql('CREATE INDEX idx_filter_rules_user_active ON filter_rules(user_id, is_active)')
                db.execute_sql('CREATE INDEX idx_filter_rules_user_category ON filter_rules(user_id, category_id)')
                db.execute_sql('CREATE INDEX idx_filter_rules_created_at ON filter_rules(created_at)')
                
                logger.info('Decreased filter_value column length back to 500 characters')
                return True
                
        except Exception as e:
            logger.error(f'Failed to rollback filter length migration: {e}')
            return False


# Create module-level migration instance
migration = IncreaseFilterValueLengthMigration()