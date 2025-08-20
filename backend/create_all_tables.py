#!/usr/bin/env python3
"""
Complete database initialization script
Creates all tables for the Zib RSS Reader application
"""

from app.core.database import db, connect_database, create_tables
from app.models.base import ALL_MODELS
from app.models.filter import FILTER_MODELS
from app.models.article import User

def main():
    print("Initializing complete database with all tables...")
    
    # Connect to database
    if not connect_database():
        print("Failed to connect to database")
        return False
    
    try:
        # Combine all models
        all_models = list(ALL_MODELS) + list(FILTER_MODELS)
        
        print(f"Creating tables for {len(all_models)} models:")
        for model in all_models:
            print(f"  - {model.__name__}")
        
        # Create all tables
        create_tables(all_models)
        
        # Create default user
        print("Creating default user...")
        try:
            user = User.create(
                username='default',
                email='default@localhost',
                password_hash='dummy',
                is_active=True
            )
            print(f"✓ Created user: {user.username}")
        except Exception as e:
            print(f"User may already exist: {e}")
        
        print("✓ Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False
    finally:
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    main()