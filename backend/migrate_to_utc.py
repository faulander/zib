#!/usr/bin/env python3
"""
Migration script to convert existing article timestamps from local time to UTC.

This script assumes that existing timestamps in the database are in local time
(without timezone info) and converts them to proper UTC timestamps.
"""

import pendulum
from app.core.database import db, init_database
from app.models.article import Article

def migrate_timestamps_to_utc():
    """Convert all existing timestamps from local time to UTC using direct SQL"""
    
    print("Starting UTC timestamp migration...")
    
    # Calculate offset from local time to UTC
    # We need to subtract the local timezone offset to convert TO UTC
    local_now = pendulum.now()
    offset_seconds = -local_now.utcoffset().total_seconds()  # Negative because we want to go TO UTC
    offset_hours = offset_seconds / 3600
    
    print(f"UTC offset: {offset_hours:+.1f} hours")
    
    # Count articles to migrate
    total_articles = Article.select().count()
    print(f"Found {total_articles} articles to migrate")
    
    with db.atomic():
        # Update article timestamps using SQL datetime function
        # Add the offset to convert local time to UTC
        sql_offset = f"{offset_hours:+.6f} hours"
        
        # Update articles table
        db.execute_sql(f"""
            UPDATE articles 
            SET 
                published_date = CASE 
                    WHEN published_date IS NOT NULL 
                    THEN datetime(published_date, '{sql_offset}')
                    ELSE NULL 
                END,
                created_at = datetime(created_at, '{sql_offset}'),
                updated_at = datetime(updated_at, '{sql_offset}')
        """)
        
        # Update feeds table
        db.execute_sql(f"""
            UPDATE feeds 
            SET 
                last_fetched = CASE 
                    WHEN last_fetched IS NOT NULL 
                    THEN datetime(last_fetched, '{sql_offset}')
                    ELSE NULL 
                END,
                created_at = datetime(created_at, '{sql_offset}'),
                updated_at = datetime(updated_at, '{sql_offset}')
        """)
        
        # Update categories table
        db.execute_sql(f"""
            UPDATE categories 
            SET 
                created_at = datetime(created_at, '{sql_offset}'),
                updated_at = datetime(updated_at, '{sql_offset}')
        """)
        
        print(f"Successfully migrated {total_articles} articles and related data to UTC")
        print(f"Applied offset: {sql_offset}")

if __name__ == '__main__':
    # Initialize database connection
    init_database()
    
    # Confirm before running
    print("\n⚠️  This will update ALL existing timestamps in the database!")
    print("Make sure you have a backup before proceeding.")
    
    response = input("\nDo you want to continue? (yes/no): ").lower().strip()
    
    if response == 'yes':
        migrate_timestamps_to_utc()
        print("\n✅ Migration completed successfully!")
    else:
        print("Migration cancelled.")