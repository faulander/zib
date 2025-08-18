#!/usr/bin/env python3
"""
Migration runner for Zib RSS Reader
Runs all migrations in sequence when starting the application
"""

import os
import sys
import importlib.util
from pathlib import Path

def run_migrations():
    """Run all migrations in the migrations directory"""
    migrations_dir = Path(__file__).parent / "migrations"
    
    if not migrations_dir.exists():
        print("No migrations directory found")
        return True
    
    # Get all migration files
    migration_files = sorted([
        f for f in migrations_dir.glob("*.py") 
        if f.name != "__init__.py" and not f.name.startswith(".")
    ])
    
    print(f"Found {len(migration_files)} migration files")
    
    success = True
    for migration_file in migration_files:
        try:
            print(f"Running migration: {migration_file.name}")
            
            # Import and run the migration
            spec = importlib.util.spec_from_file_location("migration", migration_file)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            
            # Run the migration
            if hasattr(migration_module, 'migration'):
                migration_module.migration.upgrade()
                print(f"✓ Successfully completed: {migration_file.name}")
            else:
                print(f"⚠ No migration instance found in: {migration_file.name}")
                
        except Exception as e:
            print(f"✗ Failed to run migration {migration_file.name}: {e}")
            success = False
            # Continue with other migrations instead of failing completely
    
    return success

if __name__ == "__main__":
    print("Running database migrations...")
    success = run_migrations()
    if success:
        print("All migrations completed successfully")
        sys.exit(0)
    else:
        print("Some migrations failed - check logs above")
        sys.exit(1)