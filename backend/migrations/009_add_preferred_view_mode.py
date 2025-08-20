#!/usr/bin/env python3
"""
Add preferred view mode setting to users table
"""

from app.core.database import db
from app.core.migrations import Migration

def up():
    """Apply migration"""
    print("Adding preferred_view_mode column to users table...")
    
    try:
        db.execute_sql('''
            ALTER TABLE users 
            ADD COLUMN preferred_view_mode VARCHAR(10) DEFAULT 'list'
        ''')
        
        print("✓ Added preferred_view_mode column")
        
    except Exception as e:
        if "duplicate column name" in str(e):
            print('✓ preferred_view_mode column already exists, skipping')
        else:
            print(f'✗ Migration failed: {e}')
            raise

def down():
    """Rollback migration"""
    print("Removing preferred_view_mode column from users table...")
    
    db.execute_sql('''
        ALTER TABLE users 
        DROP COLUMN preferred_view_mode
    ''')
    
    print("✓ Removed preferred_view_mode column")


class PreferredViewModeMigration(Migration):
    """Migration class for adding preferred view mode"""
    
    def up(self):
        """Apply the migration"""
        up()
    
    def down(self):
        """Rollback the migration"""
        down()


# Migration instance
migration = PreferredViewModeMigration(
    version=9,
    description="Add preferred view mode setting to users table"
)