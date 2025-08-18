#!/usr/bin/env python3
"""
Add preferred view mode setting to users table
"""

from app.core.database import db

def up():
    """Apply migration"""
    print("Adding preferred_view_mode column to users table...")
    
    db.execute_sql('''
        ALTER TABLE users 
        ADD COLUMN preferred_view_mode VARCHAR(10) DEFAULT 'list'
    ''')
    
    print("✓ Added preferred_view_mode column")

def down():
    """Rollback migration"""
    print("Removing preferred_view_mode column from users table...")
    
    db.execute_sql('''
        ALTER TABLE users 
        DROP COLUMN preferred_view_mode
    ''')
    
    print("✓ Removed preferred_view_mode column")