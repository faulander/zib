'''Add filter system for article filtering'''

from app.core.database import db
from app.models.filter import FILTER_MODELS
from peewee import OperationalError
import logging

logger = logging.getLogger(__name__)

class FilterSystemMigration:
    version = 4
    description = 'Add filter system for article filtering'
    
    def up(self):
        '''Apply migration - create filter tables'''
        try:
            with db.atomic():
                # Create filter tables
                db.create_tables(FILTER_MODELS)
                logger.info('Created filter system tables')
                
                return True
                
        except OperationalError as e:
            logger.error(f'Failed to create filter tables: {e}')
            return False
        except Exception as e:
            logger.error(f'Unexpected error in filter migration: {e}')
            return False
    
    def down(self):
        '''Rollback migration - drop filter tables'''
        try:
            with db.atomic():
                # Drop tables in reverse order to handle foreign keys
                for model in reversed(FILTER_MODELS):
                    model.drop_table(safe=True)
                logger.info('Dropped filter system tables')
                
                return True
                
        except Exception as e:
            logger.error(f'Failed to rollback filter migration: {e}')
            return False


# Create module-level migration instance
migration = FilterSystemMigration()