#!/usr/bin/env python3
"""
Migration runner for Zib RSS Reader
Uses the proper MigrationManager to track and apply migrations
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.migrations import migration_manager
from app.core.logging import get_logger

logger = get_logger(__name__)

def run_migrations():
    """Run all pending migrations using MigrationManager"""
    print("Running database migrations...")
    
    try:
        # Get migration status
        status = migration_manager.get_migration_status()
        
        if 'error' in status:
            print(f"❌ Failed to get migration status: {status['error']}")
            return False
        
        current_version = status.get('current_version', 0)
        pending_migrations = status.get('pending_migrations', [])
        
        print(f"Current database version: {current_version}")
        print(f"Pending migrations: {len(pending_migrations)}")
        
        if not pending_migrations:
            print("✅ No pending migrations")
            return True
        
        # Show what migrations will be applied
        for migration in pending_migrations:
            print(f"  - Migration {migration['version']}: {migration['description']}")
        
        # Apply migrations
        success = migration_manager.migrate()
        
        if success:
            # Get updated status
            updated_status = migration_manager.get_migration_status()
            final_version = updated_status.get('current_version', current_version)
            applied_count = len([m for m in updated_status.get('available_migrations', []) if m['applied']])
            
            print("✅ All migrations completed successfully")
            print(f"Database updated to version: {final_version}")
            print(f"Total applied migrations: {applied_count}")
        else:
            print("❌ Some migrations failed")
            
        return success
        
    except Exception as e:
        print(f"❌ Migration process failed: {e}")
        logger.error(f"Migration process failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    
    if not success:
        print("⚠️  Migrations failed, but allowing server to start (migrations might already be applied)")
        # In production, you might want to exit with error code:
        # sys.exit(1)
    
    # Always exit 0 to allow server startup for development
    # In production, you might want different behavior
    sys.exit(0)