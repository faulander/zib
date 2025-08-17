import importlib.util
from pathlib import Path
from typing import List, Optional
from peewee import DoesNotExist
from .database import db, connect_database, close_database
from .logging import get_logger
from app.models.base import SchemaVersion

logger = get_logger(__name__)


class Migration:
    '''Base migration class'''
    
    def __init__(self, version: int, description: str):
        self.version = version
        self.description = description
    
    def up(self):
        '''Apply the migration'''
        raise NotImplementedError('Migration must implement up() method')
    
    def down(self):
        '''Rollback the migration'''
        raise NotImplementedError('Migration must implement down() method')


class MigrationManager:
    '''Manages database migrations'''
    
    def __init__(self, migrations_dir: str = 'migrations'):
        # Handle both relative and absolute paths
        if Path(migrations_dir).is_absolute():
            self.migrations_dir = Path(migrations_dir)
        else:
            # Look for migrations dir relative to project root
            current_file = Path(__file__).resolve()
            backend_root = current_file.parent.parent.parent  # Go up from app/core/
            self.migrations_dir = backend_root / migrations_dir
        
        self.migrations_dir.mkdir(exist_ok=True)
        
    def get_migration_files(self) -> List[Path]:
        '''Get all migration files sorted by version'''
        migration_files = []
        
        for file_path in self.migrations_dir.glob('*.py'):
            if file_path.name.startswith('__'):
                continue  # Skip __init__.py and __pycache__
            migration_files.append(file_path)
        
        # Sort by filename (which should start with version number)
        return sorted(migration_files)
    
    def load_migration(self, file_path: Path) -> Optional[Migration]:
        '''Load a migration from a Python file'''
        try:
            spec = importlib.util.spec_from_file_location(
                f'migration_{file_path.stem}', 
                file_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for migration instance
            if hasattr(module, 'migration'):
                return module.migration
            else:
                logger.error(f'Migration file {file_path} does not have a migration instance')
                return None
                
        except Exception as e:
            logger.error(f'Failed to load migration {file_path}: {e}')
            return None
    
    def get_pending_migrations(self) -> List[Migration]:
        '''Get list of pending migrations'''
        try:
            current_version = SchemaVersion.get_current_version()
        except DoesNotExist:
            current_version = 0
        
        pending = []
        migration_files = self.get_migration_files()
        
        for file_path in migration_files:
            migration = self.load_migration(file_path)
            if migration and migration.version > current_version:
                pending.append(migration)
        
        # Sort by version
        return sorted(pending, key=lambda m: m.version)
    
    def apply_migration(self, migration: Migration) -> bool:
        '''Apply a single migration'''
        logger.info(f'Applying migration {migration.version}: {migration.description}')
        
        try:
            with db.atomic():
                # Apply migration
                migration.up()
                
                # Record in schema_version table
                SchemaVersion.create(
                    version=migration.version,
                    description=migration.description
                )
                
            logger.info(f'Successfully applied migration {migration.version}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to apply migration {migration.version}: {e}')
            return False
    
    def rollback_migration(self, migration: Migration) -> bool:
        '''Rollback a single migration'''
        logger.info(f'Rolling back migration {migration.version}: {migration.description}')
        
        try:
            with db.atomic():
                # Rollback migration
                migration.down()
                
                # Remove from schema_version table
                SchemaVersion.delete().where(
                    SchemaVersion.version == migration.version
                ).execute()
                
            logger.info(f'Successfully rolled back migration {migration.version}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to rollback migration {migration.version}: {e}')
            return False
    
    def migrate(self) -> bool:
        '''Apply all pending migrations'''
        if not connect_database():
            logger.error('Failed to connect to database')
            return False
        
        try:
            # Create schema_version table if it doesn't exist
            db.create_tables([SchemaVersion], safe=True)
            
            pending_migrations = self.get_pending_migrations()
            
            if not pending_migrations:
                logger.info('No pending migrations')
                return True
            
            logger.info(f'Found {len(pending_migrations)} pending migrations')
            
            for migration in pending_migrations:
                if not self.apply_migration(migration):
                    logger.error(f'Migration failed at version {migration.version}')
                    return False
            
            logger.info('All migrations applied successfully')
            return True
            
        except Exception as e:
            logger.error(f'Migration process failed: {e}')
            return False
        
        finally:
            close_database()
    
    def rollback_to_version(self, target_version: int) -> bool:
        '''Rollback to a specific version'''
        if not connect_database():
            logger.error('Failed to connect to database')
            return False
        
        try:
            current_version = SchemaVersion.get_current_version()
            
            if target_version >= current_version:
                logger.info(f'Already at or below version {target_version}')
                return True
            
            # Get applied migrations to rollback
            applied_migrations = []
            migration_files = self.get_migration_files()
            
            for file_path in migration_files:
                migration = self.load_migration(file_path)
                if (migration and 
                    migration.version > target_version and 
                    SchemaVersion.is_version_applied(migration.version)):
                    applied_migrations.append(migration)
            
            # Sort in reverse order for rollback
            applied_migrations.sort(key=lambda m: m.version, reverse=True)
            
            logger.info(f'Rolling back {len(applied_migrations)} migrations')
            
            for migration in applied_migrations:
                if not self.rollback_migration(migration):
                    logger.error(f'Rollback failed at version {migration.version}')
                    return False
            
            logger.info(f'Successfully rolled back to version {target_version}')
            return True
            
        except Exception as e:
            logger.error(f'Rollback process failed: {e}')
            return False
        
        finally:
            close_database()
    
    def get_migration_status(self) -> dict:
        '''Get current migration status'''
        if not connect_database():
            return {'error': 'Failed to connect to database'}
        
        try:
            current_version = SchemaVersion.get_current_version()
            migration_files = self.get_migration_files()
            
            status = {
                'current_version': current_version,
                'available_migrations': [],
                'pending_migrations': []
            }
            
            for file_path in migration_files:
                migration = self.load_migration(file_path)
                if migration:
                    migration_info = {
                        'version': migration.version,
                        'description': migration.description,
                        'applied': SchemaVersion.is_version_applied(migration.version)
                    }
                    status['available_migrations'].append(migration_info)
                    
                    if migration.version > current_version:
                        status['pending_migrations'].append(migration_info)
            
            return status
            
        except Exception as e:
            return {'error': str(e)}
        
        finally:
            close_database()


# Global migration manager instance
migration_manager = MigrationManager('migrations')


if __name__ == '__main__':
    '''Run migrations when module is executed directly'''
    print("Running database migrations...")
    if migration_manager.migrate():
        print("✅ Migrations completed successfully!")
        status = migration_manager.get_migration_status()
        print(f"Current database version: {status['current_version']}")
        print(f"Applied migrations: {len([m for m in status.get('available_migrations', []) if m['applied']])}")
    else:
        print("❌ Migrations failed! Check the logs for details.")