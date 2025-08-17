'''
OPML Import Schema Migration
Adds import job tracking tables and import metadata to existing tables
'''

from app.core.migrations import Migration
from app.core.database import db


class OPMLImportSchemaMigration(Migration):
    '''OPML import functionality schema migration'''
    
    def up(self):
        '''Create import system tables and add import tracking fields'''
        
        # Create import_jobs table
        db.execute_sql('''
            CREATE TABLE IF NOT EXISTS import_jobs (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                duplicate_strategy TEXT NOT NULL DEFAULT 'skip',
                category_parent_id INTEGER,
                validate_feeds BOOLEAN NOT NULL DEFAULT true,
                total_steps INTEGER DEFAULT 0,
                current_step INTEGER DEFAULT 0,
                current_phase TEXT,
                categories_created INTEGER DEFAULT 0,
                feeds_imported INTEGER DEFAULT 0,
                feeds_failed INTEGER DEFAULT 0,
                duplicates_found INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                error_details TEXT,
                FOREIGN KEY (category_parent_id) REFERENCES categories (id) ON DELETE SET NULL
            )
        ''')
        
        # Create import_results table
        db.execute_sql('''
            CREATE TABLE IF NOT EXISTS import_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_job_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_url TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                error_code TEXT,
                created_category_id INTEGER,
                created_feed_id INTEGER,
                existing_item_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (import_job_id) REFERENCES import_jobs (id) ON DELETE CASCADE,
                FOREIGN KEY (created_category_id) REFERENCES categories (id) ON DELETE SET NULL,
                FOREIGN KEY (created_feed_id) REFERENCES feeds (id) ON DELETE SET NULL
            )
        ''')
        
        # Create import_feed_validation table
        db.execute_sql('''
            CREATE TABLE IF NOT EXISTS import_feed_validation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_url TEXT NOT NULL UNIQUE,
                is_valid BOOLEAN NOT NULL,
                final_url TEXT,
                title TEXT,
                description TEXT,
                feed_type TEXT,
                error_message TEXT,
                error_code TEXT,
                validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        # Create indexes for import system tables
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_import_jobs_user_id ON import_jobs (user_id)')
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_import_jobs_status ON import_jobs (status)')
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_import_jobs_created_at ON import_jobs (created_at)')
        
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_import_results_job_id ON import_results (import_job_id)')
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_import_results_status ON import_results (status)')
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_import_results_item_type ON import_results (item_type)')
        
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_import_feed_validation_url ON import_feed_validation (feed_url)')
        db.execute_sql('CREATE INDEX IF NOT EXISTS idx_import_feed_validation_expires ON import_feed_validation (expires_at)')
        
        # Add import tracking columns to existing tables if they exist
        # Check if tables exist first
        tables_exist = True
        try:
            db.execute_sql('SELECT 1 FROM categories LIMIT 1')
            db.execute_sql('SELECT 1 FROM feeds LIMIT 1')
        except:
            tables_exist = False
        
        if tables_exist:
            # Check if columns already exist
            try:
                db.execute_sql('SELECT import_job_id FROM categories LIMIT 1')
            except:
                db.execute_sql('ALTER TABLE categories ADD COLUMN import_job_id TEXT')
                db.execute_sql('CREATE INDEX IF NOT EXISTS idx_categories_import_job ON categories (import_job_id)')
            
            try:
                db.execute_sql('SELECT import_job_id FROM feeds LIMIT 1')
            except:
                db.execute_sql('ALTER TABLE feeds ADD COLUMN import_job_id TEXT')
                db.execute_sql('ALTER TABLE feeds ADD COLUMN opml_title TEXT')
                db.execute_sql('ALTER TABLE feeds ADD COLUMN opml_description TEXT')
                db.execute_sql('ALTER TABLE feeds ADD COLUMN opml_html_url TEXT')
                db.execute_sql('CREATE INDEX IF NOT EXISTS idx_feeds_import_job ON feeds (import_job_id)')
        
        # Create unique constraint on import results to prevent duplicates
        db.execute_sql('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_import_results_unique 
            ON import_results (import_job_id, item_type, item_name, COALESCE(item_url, ''))
        ''')
    
    def down(self):
        '''Remove import system tables and import tracking fields'''
        
        # Drop unique constraint first
        db.execute_sql('DROP INDEX IF EXISTS idx_import_results_unique')
        
        # Drop indexes for existing table columns
        db.execute_sql('DROP INDEX IF EXISTS idx_feeds_import_job')
        db.execute_sql('DROP INDEX IF EXISTS idx_categories_import_job')
        
        # SQLite doesn't support DROP COLUMN, so we'd need to recreate tables
        # For development purposes, we'll leave the columns
        # In production, this would require table recreation with data migration
        
        # Drop indexes for import system tables
        db.execute_sql('DROP INDEX IF EXISTS idx_import_feed_validation_expires')
        db.execute_sql('DROP INDEX IF EXISTS idx_import_feed_validation_url')
        db.execute_sql('DROP INDEX IF EXISTS idx_import_results_item_type')
        db.execute_sql('DROP INDEX IF EXISTS idx_import_results_status')
        db.execute_sql('DROP INDEX IF EXISTS idx_import_results_job_id')
        db.execute_sql('DROP INDEX IF EXISTS idx_import_jobs_created_at')
        db.execute_sql('DROP INDEX IF EXISTS idx_import_jobs_status')
        db.execute_sql('DROP INDEX IF EXISTS idx_import_jobs_user_id')
        
        # Drop import system tables
        db.execute_sql('DROP TABLE IF EXISTS import_feed_validation')
        db.execute_sql('DROP TABLE IF EXISTS import_results')
        db.execute_sql('DROP TABLE IF EXISTS import_jobs')


# Migration instance
migration = OPMLImportSchemaMigration(
    version=2,
    description='OPML import system tables and import tracking fields'
)