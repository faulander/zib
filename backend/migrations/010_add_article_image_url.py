#!/usr/bin/env python3
"""
Add image_url field to articles table for storing article thumbnails
"""

from app.core.database import db

def up():
    """Apply migration"""
    print("Adding image_url column to articles table...")
    
    db.execute_sql('''
        ALTER TABLE articles 
        ADD COLUMN image_url VARCHAR(1000)
    ''')
    
    print("✓ Added image_url column")

def down():
    """Rollback migration"""
    print("Removing image_url column from articles table...")
    
    db.execute_sql('''
        ALTER TABLE articles 
        DROP COLUMN image_url
    ''')
    
    print("✓ Removed image_url column")