#!/usr/bin/env python3
"""
Database initialization for Zib RSS Reader
Creates initial database schema and default user
"""

from app.core.database import db
from app.models.base import Feed, Category
from app.models.article import User, Article, ReadStatus, UserSubscription
from app.models.filter import FilterRule

def create_tables():
    """Create all database tables"""
    try:
        db.connect()
        
        # Create all tables
        db.create_tables([
            Category,
            Feed, 
            User,
            Article,
            ReadStatus,
            UserSubscription,
            FilterRule
        ], safe=True)
        
        print("✓ Database tables created successfully")
        
        # Create default user if none exists
        if not User.select().exists():
            default_user = User.create(
                username='default',
                email='default@example.com',
                password_hash='dummy_hash',  # Will be replaced with proper auth later
                feeds_per_page=50,
                default_view='unread',
                auto_refresh_feeds=True,
                auto_refresh_interval_minutes=30
            )
            print("✓ Created default user")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to create database tables: {e}")
        return False
    finally:
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    print("Initializing database...")
    success = create_tables()
    if success:
        print("Database initialization completed successfully")
    else:
        print("Database initialization failed")
        exit(1)