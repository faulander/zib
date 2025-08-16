'''
Initial database schema migration
Creates all base tables: categories, feeds, filters, schema_version
'''

from app.core.migrations import Migration
from app.core.database import db
from app.models.base import ALL_MODELS


class InitialSchemaMigration(Migration):
    '''Initial schema creation migration'''
    
    def up(self):
        '''Create all tables with indexes'''
        # Create all model tables
        db.create_tables(ALL_MODELS)
        
        # Create additional indexes for performance
        db.execute_sql('''
            CREATE INDEX IF NOT EXISTS idx_feeds_active_category 
            ON feeds(is_active, category_id);
        ''')
        
        db.execute_sql('''
            CREATE INDEX IF NOT EXISTS idx_feeds_last_fetched 
            ON feeds(last_fetched) 
            WHERE last_fetched IS NOT NULL;
        ''')
        
        db.execute_sql('''
            CREATE INDEX IF NOT EXISTS idx_filters_active_type 
            ON filters(is_active, type);
        ''')
        
        # Create triggers for automatic timestamp updates
        db.execute_sql('''
            CREATE TRIGGER IF NOT EXISTS update_categories_timestamp 
            AFTER UPDATE ON categories
            FOR EACH ROW
            BEGIN
                UPDATE categories 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END;
        ''')
        
        db.execute_sql('''
            CREATE TRIGGER IF NOT EXISTS update_feeds_timestamp 
            AFTER UPDATE ON feeds
            FOR EACH ROW
            BEGIN
                UPDATE feeds 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END;
        ''')
        
        db.execute_sql('''
            CREATE TRIGGER IF NOT EXISTS update_filters_timestamp 
            AFTER UPDATE ON filters
            FOR EACH ROW
            BEGIN
                UPDATE filters 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END;
        ''')
    
    def down(self):
        '''Drop all tables and triggers'''
        # Drop triggers first
        db.execute_sql('DROP TRIGGER IF EXISTS update_categories_timestamp;')
        db.execute_sql('DROP TRIGGER IF EXISTS update_feeds_timestamp;')
        db.execute_sql('DROP TRIGGER IF EXISTS update_filters_timestamp;')
        
        # Drop indexes
        db.execute_sql('DROP INDEX IF EXISTS idx_feeds_active_category;')
        db.execute_sql('DROP INDEX IF EXISTS idx_feeds_last_fetched;')
        db.execute_sql('DROP INDEX IF EXISTS idx_filters_active_type;')
        
        # Drop all tables (in reverse order to handle foreign keys)
        db.drop_tables(ALL_MODELS[::-1])


# Migration instance
migration = InitialSchemaMigration(
    version=1,
    description='Initial database schema with all base tables'
)