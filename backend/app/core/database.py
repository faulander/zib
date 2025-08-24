from peewee import SqliteDatabase, Model
from pathlib import Path
import os
import time
from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


def get_database_path():
    """Get the correct database path for current environment"""
    db_path = settings.database_url.replace('sqlite:///', '')
    
    # In Docker container, use absolute path that matches volume mount
    if os.getenv('DOCKER_CONTAINER'):
        resolved_path = f'/app/{db_path}'
        logger.info(f'Docker environment detected, using path: {resolved_path}')
        return resolved_path
    
    # For local development, use relative to backend directory
    if not os.path.isabs(db_path):
        backend_dir = Path(__file__).parent.parent.parent
        resolved_path = str(backend_dir / db_path)
        logger.info(f'Local environment detected, using path: {resolved_path}')
        return resolved_path
    
    logger.info(f'Using absolute path: {db_path}')
    return db_path


def log_database_environment():
    """Log detailed database environment information for debugging"""
    logger.info('=== DATABASE ENVIRONMENT DEBUG ===')
    logger.info(f'Environment: {"Docker" if os.getenv("DOCKER_CONTAINER") else "Local"}')
    logger.info(f'Working directory: {os.getcwd()}')
    logger.info(f'Database URL from config: {settings.database_url}')
    
    db_path = get_database_path()
    logger.info(f'Resolved database path: {db_path}')
    logger.info(f'Database file exists: {Path(db_path).exists()}')
    
    if Path(db_path).exists():
        stat = Path(db_path).stat()
        logger.info(f'Database file size: {stat.st_size} bytes')
        logger.info(f'Database file modified: {time.ctime(stat.st_mtime)}')
    
    db_dir = Path(db_path).parent
    logger.info(f'Database directory: {db_dir}')
    logger.info(f'Database directory exists: {db_dir.exists()}')
    
    if db_dir.exists():
        try:
            contents = list(db_dir.glob('*'))
            logger.info(f'Database directory contents: {contents}')
        except Exception as e:
            logger.warning(f'Could not list directory contents: {e}')
    
    # Check volume mount in Docker
    if os.getenv('DOCKER_CONTAINER'):
        logger.info('=== DOCKER VOLUME DEBUG ===')
        try:
            # Check if /proc/mounts exists and is readable
            if Path('/proc/mounts').exists():
                mount_info = Path('/proc/mounts').read_text()
                for line in mount_info.splitlines():
                    if '/app/data' in line:
                        logger.info(f'Volume mount: {line}')
            else:
                logger.info('/proc/mounts not accessible')
        except Exception as e:
            logger.warning(f'Could not check volume mounts: {e}')
    
    logger.info('=== END DATABASE DEBUG ===')


def ensure_database_directory():
    """Ensure database directory exists and is properly mounted"""
    db_path = get_database_path()
    db_dir = Path(db_path).parent
    
    logger.info(f'Checking database directory: {db_dir}')
    
    if not db_dir.exists():
        if os.getenv('DOCKER_CONTAINER'):
            # In Docker, the volume should already be mounted
            logger.warning(f'Database directory {db_dir} not found in Docker container')
            logger.warning('This may indicate a volume mounting issue')
        
        logger.info(f'Creating database directory: {db_dir}')
        db_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify directory is writable
    test_file = db_dir / '.write_test'
    try:
        test_file.touch()
        test_file.unlink()
        logger.info(f'Database directory {db_dir} is writable')
    except Exception as e:
        logger.error(f'Database directory {db_dir} is not writable: {e}')
        raise


# Get database path using the new function
db_path = get_database_path()

# Database instance
db = SqliteDatabase(
    db_path,
    pragmas={
        'journal_mode': 'wal',
        'cache_size': -1 * 64000,  # 64MB
        'foreign_keys': 1,
        'ignore_check_constraints': 0,
        'synchronous': 1,
    }
)


class BaseModel(Model):
    '''Base model class for all database models'''
    
    class Meta:
        database = db


def connect_database():
    '''Connect to the database'''
    try:
        if db.is_closed():
            db.connect()
            logger.info(f'Connected to database: {settings.database_url}')
        return True
    except Exception as e:
        logger.error(f'Failed to connect to database: {e}')
        return False


def close_database():
    '''Close database connection'''
    try:
        if not db.is_closed():
            db.close()
            logger.info('Database connection closed')
    except Exception as e:
        logger.error(f'Error closing database: {e}')


def create_tables(models):
    '''Create database tables for given models'''
    try:
        db.create_tables(models)
        logger.info(f'Created tables for models: {[m.__name__ for m in models]}')
    except Exception as e:
        logger.error(f'Error creating tables: {e}')
        raise


def drop_tables(models):
    '''Drop database tables for given models'''
    try:
        db.drop_tables(models)
        logger.info(f'Dropped tables for models: {[m.__name__ for m in models]}')
    except Exception as e:
        logger.error(f'Error dropping tables: {e}')
        raise


def safe_database_initialization():
    """Initialize database with existing data preservation"""
    # Log database environment for debugging
    log_database_environment()
    
    # Ensure database directory exists and is writable
    ensure_database_directory()
    
    db_path = get_database_path()
    
    # Check if database already exists
    db_exists = Path(db_path).exists()
    logger.info(f'Database exists: {db_exists} at path: {db_path}')
    
    if db_exists:
        # Database exists - verify it's valid and run migrations only
        logger.info('Existing database found, running migrations only')
        
        # Check database integrity
        try:
            with DatabaseManager():
                db.execute_sql('SELECT COUNT(*) FROM sqlite_master')
                logger.info('Existing database is valid')
        except Exception as e:
            logger.error(f'Existing database is corrupted: {e}')
            
            # Create backup before any recovery attempts
            backup_path = f'{db_path}.backup.{int(time.time())}'
            logger.info(f'Creating backup at: {backup_path}')
            try:
                Path(db_path).rename(backup_path)
                logger.info('Database backup created successfully')
            except Exception as backup_error:
                logger.error(f'Failed to create backup: {backup_error}')
                raise
            
            logger.warning('Database corrupted, will create new database')
            db_exists = False
    
    if not db_exists:
        logger.info('No existing database, creating new database')
    
    # Connect and run migrations
    if not connect_database():
        raise Exception('Failed to connect to database')
    
    try:
        # Run migrations (should be safe for both new and existing databases)
        from .migrations import migration_manager
        if migration_manager.migrate():
            logger.info('Database initialization/migration completed successfully')
            
            # Log some basic stats to verify data preservation
            try:
                with DatabaseManager():
                    from app.models.base import User
                    from app.models.filter import FilterRule
                    
                    user_count = User.select().count()
                    filter_count = FilterRule.select().count()
                    
                    logger.info(f'Database stats: {user_count} users, {filter_count} filters')
                    
                    if db_exists and (user_count > 0 or filter_count > 0):
                        logger.info('✅ Existing data preserved during migration')
                    elif not db_exists:
                        logger.info('✅ New database created successfully')
                    else:
                        logger.warning('⚠️ Database exists but no data found - possible data loss')
                        
            except Exception as e:
                logger.warning(f'Could not retrieve database stats: {e}')
        else:
            raise Exception('Database migration failed')
            
    except Exception as e:
        logger.error(f'Database initialization failed: {e}')
        close_database()
        raise


def init_database():
    '''Initialize database connection and run migrations (legacy wrapper)'''
    logger.info('Initializing database (using safe initialization)...')
    safe_database_initialization()


class DatabaseManager:
    '''Context manager for database connections'''
    
    def __init__(self, auto_connect=True):
        self.auto_connect = auto_connect
        self.was_closed = False
    
    def __enter__(self):
        if self.auto_connect:
            self.was_closed = db.is_closed()
            if self.was_closed:
                connect_database()
        return db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.auto_connect and self.was_closed:
            close_database()


class TransactionManager:
    '''Context manager for database transactions'''
    
    def __init__(self, rollback_on_error=True):
        self.rollback_on_error = rollback_on_error
        self.transaction = None
    
    def __enter__(self):
        if db.is_closed():
            connect_database()
        
        self.transaction = db.atomic()
        return self.transaction.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            return self.transaction.__exit__(exc_type, exc_val, exc_tb)
        except Exception as e:
            if self.rollback_on_error:
                logger.error(f'Transaction failed, rolling back: {e}')
                raise
            else:
                logger.warning(f'Transaction completed with error: {e}')
                return False


def health_check():
    '''Check database connection health'''
    try:
        with DatabaseManager():
            # Simple query to test connection
            db.execute_sql('SELECT 1')
            return {'status': 'healthy', 'database': 'connected'}
    except Exception as e:
        logger.error(f'Database health check failed: {e}')
        return {'status': 'unhealthy', 'error': str(e)}