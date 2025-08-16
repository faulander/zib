from typing import List, Dict, Any
from peewee import DoesNotExist, IntegrityError
from app.models.base import Category, Feed
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.core.exceptions import CategoryException, ValidationException
from app.core.database import TransactionManager
from app.core.logging import get_logger

logger = get_logger(__name__)


class CategoryService:
    '''Service class for Category business logic'''
    
    @staticmethod
    def create_category(category_data: CategoryCreate) -> CategoryResponse:
        '''Create a new category'''
        try:
            with TransactionManager():
                # Check if name already exists
                existing_category = Category.select().where(Category.name == category_data.name).first()
                if existing_category:
                    raise ValidationException(
                        f'Category with name "{category_data.name}" already exists',
                        {'name': category_data.name, 'existing_id': existing_category.id}
                    )
                
                # Create category
                category = Category.create(
                    name=category_data.name,
                    description=category_data.description,
                    color=category_data.color
                )
                
                logger.info(f'Created category: {category.id} - {category.name}')
                return CategoryResponse.model_validate(category)
                
        except IntegrityError as e:
            logger.error(f'Database integrity error creating category: {e}')
            raise ValidationException(
                'Category creation failed due to data constraint violation',
                {'error': str(e)}
            )
        except Exception as e:
            logger.error(f'Unexpected error creating category: {e}')
            raise CategoryException(
                'Failed to create category',
                {'error': str(e)}
            )
    
    @staticmethod
    def get_category_by_id(category_id: int) -> CategoryResponse:
        '''Get category by ID'''
        try:
            category = Category.get_by_id(category_id)
            return CategoryResponse.model_validate(category)
            
        except DoesNotExist:
            raise CategoryException(
                f'Category with ID {category_id} not found',
                {'category_id': category_id}
            )
        except Exception as e:
            logger.error(f'Error retrieving category {category_id}: {e}')
            raise CategoryException(
                'Failed to retrieve category',
                {'category_id': category_id, 'error': str(e)}
            )
    
    @staticmethod
    def update_category(category_id: int, category_data: CategoryUpdate) -> CategoryResponse:
        '''Update an existing category'''
        try:
            with TransactionManager():
                # Get existing category
                try:
                    category = Category.get_by_id(category_id)
                except DoesNotExist:
                    raise CategoryException(
                        f'Category with ID {category_id} not found',
                        {'category_id': category_id}
                    )
                
                # Check for name conflicts if name is being updated
                if category_data.name and category_data.name != category.name:
                    existing_category = Category.select().where(
                        (Category.name == category_data.name) & (Category.id != category_id)
                    ).first()
                    if existing_category:
                        raise ValidationException(
                            f'Category with name "{category_data.name}" already exists',
                            {'name': category_data.name, 'existing_id': existing_category.id}
                        )
                
                # Update fields that are provided
                update_data = category_data.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(category, field, value)
                
                category.save()
                
                logger.info(f'Updated category: {category.id} - {category.name}')
                return CategoryResponse.model_validate(category)
                
        except ValidationException:
            raise
        except CategoryException:
            raise
        except IntegrityError as e:
            logger.error(f'Database integrity error updating category: {e}')
            raise ValidationException(
                'Category update failed due to data constraint violation',
                {'error': str(e)}
            )
        except Exception as e:
            logger.error(f'Unexpected error updating category {category_id}: {e}')
            raise CategoryException(
                'Failed to update category',
                {'category_id': category_id, 'error': str(e)}
            )
    
    @staticmethod
    def delete_category(category_id: int) -> Dict[str, Any]:
        '''Delete a category'''
        try:
            with TransactionManager():
                try:
                    category = Category.get_by_id(category_id)
                except DoesNotExist:
                    raise CategoryException(
                        f'Category with ID {category_id} not found',
                        {'category_id': category_id}
                    )
                
                # Check if category has feeds
                feed_count = Feed.select().where(Feed.category == category_id).count()
                if feed_count > 0:
                    raise ValidationException(
                        f'Cannot delete category with {feed_count} associated feeds',
                        {'category_id': category_id, 'feed_count': feed_count}
                    )
                
                category_name = category.name
                category.delete_instance()
                
                logger.info(f'Deleted category: {category_id} - {category_name}')
                return {
                    'message': f'Category "{category_name}" deleted successfully',
                    'category_id': category_id,
                    'name': category_name
                }
                
        except ValidationException:
            raise
        except CategoryException:
            raise
        except Exception as e:
            logger.error(f'Unexpected error deleting category {category_id}: {e}')
            raise CategoryException(
                'Failed to delete category',
                {'category_id': category_id, 'error': str(e)}
            )
    
    @staticmethod
    def list_categories() -> List[CategoryResponse]:
        '''List all categories'''
        try:
            categories = Category.select().order_by(Category.name)
            return [CategoryResponse.model_validate(category) for category in categories]
            
        except Exception as e:
            logger.error(f'Error listing categories: {e}')
            raise CategoryException(
                'Failed to retrieve categories',
                {'error': str(e)}
            )