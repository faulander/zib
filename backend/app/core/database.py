from peewee import SqliteDatabase, Model
from .config import settings
from .logging import get_logger

logger = get_logger(__name__)

# Database instance
db = SqliteDatabase(
    settings.database_url.replace('sqlite:///', ''),
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


def init_database():
    '''Initialize database connection and run migrations'''
    from .migrations import migration_manager
    
    logger.info('Initializing database...')
    
    if not connect_database():
        raise Exception('Failed to connect to database')
    
    try:
        # Run migrations
        if migration_manager.migrate():
            logger.info('Database initialization completed successfully')
        else:
            raise Exception('Database migration failed')
            
    except Exception as e:
        logger.error(f'Database initialization failed: {e}')
        close_database()
        raise


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