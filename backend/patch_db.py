#!/usr/bin/env python3
"""
Database patch script to add missing columns
This runs after database initialization to ensure all required columns exist
"""

import sqlite3
import os
from pathlib import Path

def patch_database():
    """Add missing columns that migrations might have missed"""
    db_path = Path(__file__).parent / "data" / "zib.db"
    
    if not db_path.exists():
        print("Database file not found, skipping patch")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add missing columns if they don't exist
        columns_to_add = [
            ("users", "open_webpage_for_short_articles", "BOOLEAN DEFAULT 0"),
            ("users", "short_article_threshold", "INTEGER DEFAULT 500"),
            ("users", "preferred_view_mode", "VARCHAR(50) DEFAULT 'cards'"),
            ("users", "auto_refresh_feeds", "BOOLEAN DEFAULT 1"),
            ("users", "auto_refresh_interval_minutes", "INTEGER DEFAULT 60"),
            ("articles", "image_url", "TEXT"),
        ]
        
        for table, column, definition in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                print(f"✓ Added column {column} to {table}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"✓ Column {column} already exists in {table}")
                else:
                    print(f"✗ Failed to add {column} to {table}: {e}")
        
        conn.commit()
        print("Database patch completed successfully")
        
    except Exception as e:
        print(f"Database patch failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    patch_database()