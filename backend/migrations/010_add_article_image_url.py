#!/usr/bin/env python3
"""
Add image_url field to articles table for storing article thumbnails
"""

from app.core.database import db
from app.core.migrations import Migration

def up():
    """Apply migration"""
    print("Adding image_url column to articles table...")
    
    try:
        db.execute_sql('''
            ALTER TABLE articles 
            ADD COLUMN image_url VARCHAR(1000)
        ''')
        
        print("✓ Added image_url column")
        
    except Exception as e:
        if "duplicate column name" in str(e):
            print('✓ image_url column already exists, skipping')
        else:
            print(f'✗ Migration failed: {e}')
            raise

def down():
    """Rollback migration"""
    print("Removing image_url column from articles table...")
    
    db.execute_sql('''
        ALTER TABLE articles 
        DROP COLUMN image_url
    ''')
    
    print("✓ Removed image_url column")


class ArticleImageUrlMigration(Migration):
    """Migration class for adding article image URL"""
    
    def up(self):
        """Apply the migration"""
        up()
    
    def down(self):
        """Rollback the migration"""
        down()


# Migration instance
migration = ArticleImageUrlMigration(
    version=10,
    description="Add image_url field to articles table for storing article thumbnails"
)