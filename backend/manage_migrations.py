#!/usr/bin/env python3
"""
Migration management tool for Zib RSS Reader
Provides commands for applying, rolling back, and managing database migrations
"""

import sys
import argparse
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.migrations import migration_manager
from app.core.logging import get_logger

logger = get_logger(__name__)

def migrate_command():
    """Apply all pending migrations"""
    print("Applying pending migrations...")
    
    status = migration_manager.get_migration_status()
    if 'error' in status:
        print(f"❌ Error getting migration status: {status['error']}")
        return False
    
    pending_migrations = status.get('pending_migrations', [])
    if not pending_migrations:
        print("✅ No pending migrations")
        return True
    
    print(f"Found {len(pending_migrations)} pending migrations:")
    for migration in pending_migrations:
        print(f"  - Migration {migration['version']}: {migration['description']}")
    
    if migration_manager.migrate():
        print("✅ All migrations applied successfully")
        return True
    else:
        print("❌ Migration failed")
        return False

def rollback_command(target_version):
    """Rollback to a specific version"""
    print(f"Rolling back to version {target_version}...")
    
    status = migration_manager.get_migration_status()
    if 'error' in status:
        print(f"❌ Error getting migration status: {status['error']}")
        return False
    
    current_version = status.get('current_version', 0)
    if target_version >= current_version:
        print(f"✅ Already at or below version {target_version}")
        return True
    
    if migration_manager.rollback_to_version(target_version):
        print(f"✅ Successfully rolled back to version {target_version}")
        return True
    else:
        print("❌ Rollback failed")
        return False

def status_command():
    """Show migration status"""
    status = migration_manager.get_migration_status()
    
    if 'error' in status:
        print(f"❌ Error getting migration status: {status['error']}")
        return False
    
    current_version = status.get('current_version', 0)
    available_migrations = status.get('available_migrations', [])
    pending_migrations = status.get('pending_migrations', [])
    
    print(f"Current database version: {current_version}")
    print(f"Total available migrations: {len(available_migrations)}")
    print(f"Pending migrations: {len(pending_migrations)}")
    
    if available_migrations:
        print("\nMigration history:")
        for migration in sorted(available_migrations, key=lambda m: m['version']):
            status_icon = "✅" if migration['applied'] else "⏳"
            print(f"  {status_icon} Migration {migration['version']}: {migration['description']}")
    
    if pending_migrations:
        print("\nPending migrations:")
        for migration in pending_migrations:
            print(f"  ⏳ Migration {migration['version']}: {migration['description']}")
    else:
        print("\n✅ All migrations are up to date")
    
    return True

def create_migration_command(description):
    """Create a new migration template"""
    status = migration_manager.get_migration_status()
    if 'error' in status:
        print(f"❌ Error getting migration status: {status['error']}")
        return False
    
    current_version = status.get('current_version', 0)
    next_version = current_version + 1
    
    # Pad version number to 3 digits
    version_str = f"{next_version:03d}"
    
    # Create filename
    safe_description = "".join(c if c.isalnum() else "_" for c in description.lower())
    filename = f"{version_str}_{safe_description}.py"
    filepath = migration_manager.migrations_dir / filename
    
    template = f'''#!/usr/bin/env python3
"""
{description}
"""

from app.core.database import db
from app.core.migrations import Migration
from playhouse.migrate import SqliteMigrator, migrate
from datetime import datetime
from peewee import DateTimeField, BooleanField, IntegerField, CharField, TextField

def up():
    """Apply migration"""
    print("Applying migration: {description}")
    
    migrator = SqliteMigrator(db)
    
    # Add your migration logic here
    # Examples:
    # migrate(
    #     migrator.add_column('table_name', 'new_column', CharField(default=''))
    # )
    # 
    # Or create new tables:
    # db.execute_sql("""
    #     CREATE TABLE new_table (
    #         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         name VARCHAR(255) NOT NULL,
    #         created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    #     )
    # """)
    
    print("✓ Migration applied successfully")

def down():
    """Rollback migration"""
    print("Rolling back migration: {description}")
    
    migrator = SqliteMigrator(db)
    
    # Add your rollback logic here
    # Examples:
    # migrate(
    #     migrator.drop_column('table_name', 'new_column')
    # )
    # 
    # Or drop tables:
    # db.execute_sql("DROP TABLE IF EXISTS new_table")
    
    print("✓ Migration rolled back successfully")


class Migration{next_version:03d}(Migration):
    """Migration class for {description}"""
    
    def up(self):
        """Apply the migration"""
        up()
    
    def down(self):
        """Rollback the migration"""
        down()


# Migration instance
migration = Migration{next_version:03d}(
    version={next_version},
    description="{description}"
)
'''
    
    try:
        with open(filepath, 'w') as f:
            f.write(template)
        
        print(f"✅ Created migration file: {filepath}")
        print(f"Migration version: {next_version}")
        print(f"Description: {description}")
        print(f"\nEdit the migration file and add your up() and down() logic.")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create migration file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Zib RSS Reader Migration Manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Apply all pending migrations')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to specific version')
    rollback_parser.add_argument('version', type=int, help='Target version to rollback to')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show migration status')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new migration')
    create_parser.add_argument('description', help='Migration description')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    success = True
    
    try:
        if args.command == 'migrate':
            success = migrate_command()
        elif args.command == 'rollback':
            success = rollback_command(args.version)
        elif args.command == 'status':
            success = status_command()
        elif args.command == 'create':
            success = create_migration_command(args.description)
        else:
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()
            success = False
            
    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user")
        success = False
    except Exception as e:
        print(f"❌ Migration command failed: {e}")
        logger.error(f"Migration command failed: {e}")
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()