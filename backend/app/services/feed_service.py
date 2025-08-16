from typing import List, Optional, Dict, Any
from peewee import DoesNotExist, IntegrityError
from app.models.base import Feed, Category
from app.schemas.feed import FeedCreate, FeedUpdate, FeedResponse
from app.schemas.common import PaginatedResponse
from app.core.exceptions import FeedException, ValidationException
from app.core.database import TransactionManager
from app.core.logging import get_logger

logger = get_logger(__name__)


class FeedService:
    '''Service class for Feed business logic'''
    
    @staticmethod
    def create_feed(feed_data: FeedCreate) -> FeedResponse:
        '''Create a new feed'''
        try:
            with TransactionManager():
                # Check if URL already exists
                existing_feed = Feed.select().where(Feed.url == feed_data.url).first()
                if existing_feed:
                    raise ValidationException(
                        f'Feed with URL {feed_data.url} already exists',
                        {'url': feed_data.url, 'existing_id': existing_feed.id}
                    )
                
                # Validate category exists if provided
                if feed_data.category_id:
                    try:
                        Category.get_by_id(feed_data.category_id)
                    except DoesNotExist:
                        raise ValidationException(
                            f'Category with ID {feed_data.category_id} not found',
                            {'category_id': feed_data.category_id}
                        )
                
                # Create feed
                feed = Feed.create(
                    url=feed_data.url,
                    title=feed_data.title,
                    description=feed_data.description,
                    category_id=feed_data.category_id,
                    fetch_interval=feed_data.fetch_interval
                )
                
                logger.info(f'Created feed: {feed.id} - {feed.url}')
                return FeedResponse.model_validate(feed)
                
        except IntegrityError as e:
            logger.error(f'Database integrity error creating feed: {e}')
            raise ValidationException(
                'Feed creation failed due to data constraint violation',
                {'error': str(e)}
            )
        except Exception as e:
            logger.error(f'Unexpected error creating feed: {e}')
            raise FeedException(
                'Failed to create feed',
                {'error': str(e)}
            )
    
    @staticmethod
    def get_feed_by_id(feed_id: int, include_category: bool = False) -> FeedResponse:
        '''Get feed by ID'''
        try:
            if include_category:
                feed = (Feed
                       .select(Feed, Category)
                       .join(Category, on=(Feed.category == Category.id), join_type='LEFT OUTER')
                       .where(Feed.id == feed_id)
                       .get())
            else:
                feed = Feed.get_by_id(feed_id)
            
            return FeedResponse.model_validate(feed)
            
        except DoesNotExist:
            raise FeedException(
                f'Feed with ID {feed_id} not found',
                {'feed_id': feed_id}
            )
        except Exception as e:
            logger.error(f'Error retrieving feed {feed_id}: {e}')
            raise FeedException(
                'Failed to retrieve feed',
                {'feed_id': feed_id, 'error': str(e)}
            )
    
    @staticmethod
    def update_feed(feed_id: int, feed_data: FeedUpdate) -> FeedResponse:
        '''Update an existing feed'''
        try:
            with TransactionManager():
                # Get existing feed
                try:
                    feed = Feed.get_by_id(feed_id)
                except DoesNotExist:
                    raise FeedException(
                        f'Feed with ID {feed_id} not found',
                        {'feed_id': feed_id}
                    )
                
                # Validate category exists if being updated
                if feed_data.category_id is not None and feed_data.category_id != feed.category_id:
                    try:
                        Category.get_by_id(feed_data.category_id)
                    except DoesNotExist:
                        raise ValidationException(
                            f'Category with ID {feed_data.category_id} not found',
                            {'category_id': feed_data.category_id}
                        )
                
                # Check for URL conflicts if URL is being updated
                if feed_data.url and feed_data.url != feed.url:
                    existing_feed = Feed.select().where(
                        (Feed.url == feed_data.url) & (Feed.id != feed_id)
                    ).first()
                    if existing_feed:
                        raise ValidationException(
                            f'Feed with URL {feed_data.url} already exists',
                            {'url': feed_data.url, 'existing_id': existing_feed.id}
                        )
                
                # Update fields that are provided
                update_data = feed_data.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(feed, field, value)
                
                feed.save()
                
                logger.info(f'Updated feed: {feed.id} - {feed.url}')
                return FeedResponse.model_validate(feed)
                
        except ValidationException:
            raise
        except FeedException:
            raise
        except IntegrityError as e:
            logger.error(f'Database integrity error updating feed: {e}')
            raise ValidationException(
                'Feed update failed due to data constraint violation',
                {'error': str(e)}
            )
        except Exception as e:
            logger.error(f'Unexpected error updating feed {feed_id}: {e}')
            raise FeedException(
                'Failed to update feed',
                {'feed_id': feed_id, 'error': str(e)}
            )
    
    @staticmethod
    def delete_feed(feed_id: int) -> Dict[str, Any]:
        '''Delete a feed'''
        try:
            with TransactionManager():
                try:
                    feed = Feed.get_by_id(feed_id)
                except DoesNotExist:
                    raise FeedException(
                        f'Feed with ID {feed_id} not found',
                        {'feed_id': feed_id}
                    )
                
                feed_url = feed.url
                feed.delete_instance()
                
                logger.info(f'Deleted feed: {feed_id} - {feed_url}')
                return {
                    'message': f'Feed {feed_id} deleted successfully',
                    'feed_id': feed_id,
                    'url': feed_url
                }
                
        except FeedException:
            raise
        except Exception as e:
            logger.error(f'Unexpected error deleting feed {feed_id}: {e}')
            raise FeedException(
                'Failed to delete feed',
                {'feed_id': feed_id, 'error': str(e)}
            )
    
    @staticmethod
    def list_feeds(
        page: int = 1,
        page_size: int = 10,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        include_category: bool = False
    ) -> PaginatedResponse:
        '''List feeds with pagination and filtering'''
        try:
            # Build query
            if include_category:
                query = (Feed
                        .select(Feed, Category)
                        .join(Category, on=(Feed.category == Category.id), join_type='LEFT OUTER'))
            else:
                query = Feed.select()
            
            # Apply filters
            if category_id is not None:
                query = query.where(Feed.category == category_id)
            
            if is_active is not None:
                query = query.where(Feed.is_active == is_active)
            
            # Get total count
            total = query.count()
            
            # Calculate pagination
            offset = (page - 1) * page_size
            pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
            
            # Apply pagination
            feeds = query.offset(offset).limit(page_size)
            
            # Convert to response format
            items = []
            for feed in feeds:
                feed_data = FeedResponse.model_validate(feed)
                items.append(feed_data.model_dump())
            
            return PaginatedResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f'Error listing feeds: {e}')
            raise FeedException(
                'Failed to retrieve feeds',
                {'error': str(e)}
            )
    
    @staticmethod
    def get_feeds_by_category(category_id: int) -> List[FeedResponse]:
        '''Get all feeds in a specific category'''
        try:
            # Validate category exists
            try:
                Category.get_by_id(category_id)
            except DoesNotExist:
                raise ValidationException(
                    f'Category with ID {category_id} not found',
                    {'category_id': category_id}
                )
            
            feeds = Feed.select().where(Feed.category == category_id)
            return [FeedResponse.model_validate(feed) for feed in feeds]
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f'Error getting feeds by category {category_id}: {e}')
            raise FeedException(
                'Failed to retrieve feeds by category',
                {'category_id': category_id, 'error': str(e)}
            )
    
    @staticmethod
    def update_feed_status(feed_id: int, is_active: bool) -> FeedResponse:
        '''Update feed active status'''
        try:
            with TransactionManager():
                try:
                    feed = Feed.get_by_id(feed_id)
                except DoesNotExist:
                    raise FeedException(
                        f'Feed with ID {feed_id} not found',
                        {'feed_id': feed_id}
                    )
                
                feed.is_active = is_active
                feed.save()
                
                status = 'activated' if is_active else 'deactivated'
                logger.info(f'{status.capitalize()} feed: {feed.id} - {feed.url}')
                
                return FeedResponse.model_validate(feed)
                
        except FeedException:
            raise
        except Exception as e:
            logger.error(f'Error updating feed status {feed_id}: {e}')
            raise FeedException(
                'Failed to update feed status',
                {'feed_id': feed_id, 'error': str(e)}
            )