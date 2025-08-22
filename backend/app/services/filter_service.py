import logging
import pendulum
from typing import List, Optional
from peewee import DoesNotExist

from app.models.filter import FilterRule
from app.models.article import User, Article
from app.models.base import Category
from app.core.database import TransactionManager
from app.core.exceptions import ValidationException

logger = logging.getLogger(__name__)


class FilterService:
    '''Service for managing article filters'''
    
    @staticmethod
    def create_filter(user: User, filter_data: dict) -> FilterRule:
        '''Create a new filter rule'''
        try:
            with TransactionManager():
                # Validate category if provided
                category = None
                if filter_data.get('category_id'):
                    try:
                        category = Category.get_by_id(filter_data['category_id'])
                    except DoesNotExist:
                        raise ValidationException(
                            f"Category {filter_data['category_id']} not found"
                        )
                
                # Create filter rule
                filter_rule = FilterRule.create(
                    user=user,
                    name=filter_data['name'],
                    filter_type=filter_data.get('filter_type', 'title_contains'),
                    filter_value=filter_data['filter_value'],
                    category=category,
                    feed_id=filter_data.get('feed_id'),
                    is_active=filter_data.get('is_active', True),
                    case_sensitive=filter_data.get('case_sensitive', False)
                )
                
                logger.info(f'Created filter rule: {filter_rule.name} for user {user.username}')
                return filter_rule
                
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f'Failed to create filter rule: {e}')
            raise ValidationException(f'Failed to create filter: {str(e)}')
    
    @staticmethod
    def get_user_filters(user: User, active_only: bool = False) -> List[FilterRule]:
        '''Get all filters for a user'''
        try:
            query = FilterRule.select().where(FilterRule.user == user)
            
            if active_only:
                query = query.where(FilterRule.is_active == True)
            
            return list(query.order_by(FilterRule.created_at.desc()))
            
        except Exception as e:
            logger.error(f'Failed to get filters for user {user.username}: {e}')
            return []
    
    @staticmethod
    def get_filter(filter_id: int, user: User) -> FilterRule:
        '''Get a specific filter rule'''
        try:
            return FilterRule.get(
                (FilterRule.id == filter_id) & 
                (FilterRule.user == user)
            )
        except DoesNotExist:
            raise ValidationException(f'Filter {filter_id} not found')
    
    @staticmethod
    def update_filter(filter_id: int, user: User, filter_data: dict) -> FilterRule:
        '''Update a filter rule'''
        try:
            with TransactionManager():
                filter_rule = FilterService.get_filter(filter_id, user)
                
                # Update category if provided
                if 'category_id' in filter_data:
                    if filter_data['category_id']:
                        try:
                            filter_rule.category = Category.get_by_id(filter_data['category_id'])
                        except DoesNotExist:
                            raise ValidationException(
                                f"Category {filter_data['category_id']} not found"
                            )
                    else:
                        filter_rule.category = None
                
                # Update other fields
                for field in ['name', 'filter_type', 'filter_value', 'feed_id', 
                              'is_active', 'case_sensitive']:
                    if field in filter_data:
                        setattr(filter_rule, field, filter_data[field])
                
                filter_rule.save()
                logger.info(f'Updated filter rule: {filter_rule.id}')
                return filter_rule
                
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f'Failed to update filter {filter_id}: {e}')
            raise ValidationException(f'Failed to update filter: {str(e)}')
    
    @staticmethod
    def delete_filter(filter_id: int, user: User) -> bool:
        '''Delete a filter rule'''
        try:
            with TransactionManager():
                filter_rule = FilterService.get_filter(filter_id, user)
                filter_rule.delete_instance()
                logger.info(f'Deleted filter rule: {filter_id}')
                return True
                
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f'Failed to delete filter {filter_id}: {e}')
            raise ValidationException(f'Failed to delete filter: {str(e)}')
    
    @staticmethod
    def apply_filters(articles: List[Article], user: User, category_id: Optional[int] = None) -> List[Article]:
        '''Apply user's active filters to a list of articles'''
        try:
            
            # Get active filters for this user
            filters = FilterRule.select().where(
                (FilterRule.user == user) & 
                (FilterRule.is_active == True)
            )
            
            # If category specified, get filters for that category or global filters
            if category_id:
                filters = filters.where(
                    (FilterRule.category == category_id) | 
                    (FilterRule.category.is_null())
                )
            else:
                # Only global filters
                filters = filters.where(FilterRule.category.is_null())
            
            filters = list(filters)
            
            logger.debug(f'Found {len(filters)} active filters for user {user.username}')
            for f in filters:
                logger.debug(f'  Filter: {f.name} ({f.filter_type}: "{f.filter_value}")')
            
            if not filters:
                logger.debug('No active filters found, returning all articles')
                return articles
            
            # Get today's date for comparison
            today = pendulum.now('UTC').date()
            
            # Apply each filter
            filtered_articles = []
            for article in articles:
                should_filter = False
                
                # Check if article is unread and from today - if so, bypass filters
                article_date = None
                if article.published_date:
                    # Parse the UTC date string and get the date part
                    article_date = pendulum.parse(str(article.published_date)).date()
                elif article.created_at:
                    article_date = pendulum.parse(str(article.created_at)).date()
                
                # Check if article is read for this user
                from app.models.article import ReadStatus
                try:
                    read_status = ReadStatus.get((ReadStatus.user == user) & (ReadStatus.article == article))
                    article_is_read = read_status.is_read
                except:
                    article_is_read = False  # Default to unread if no status exists
                
                # Apply filtering for this article
                for filter_rule in filters:
                    # Check if filter applies to this article's feed
                    if filter_rule.feed_id and article.feed_id != filter_rule.feed_id:
                        continue
                    
                    # Check if article matches filter (should be hidden)
                    if filter_rule.matches(article.title, article.author):
                        # Content filters (like [premium]) ALWAYS apply regardless of date/read status
                        if '[premium]' in filter_rule.filter_value.lower() or 'premium' in filter_rule.name.lower():
                            logger.debug(f'Content filter matched - filtering out article: "{article.title}" (matched filter: {filter_rule.name})')
                            should_filter = True
                            break
                        # Other filters allow unread articles from today to bypass
                        elif not article_is_read and article_date == today:
                            logger.debug(f'Non-content filter bypassed for today\'s unread article: "{article.title}" (filter: {filter_rule.name})')
                            continue
                        else:
                            logger.debug(f'Filtering out article: "{article.title}" (matched filter: {filter_rule.name})')
                            should_filter = True
                            break
                
                if not should_filter:
                    filtered_articles.append(article)
            
            logger.info(f'Applied filters: {len(articles)} -> {len(filtered_articles)} articles (filtered {len(articles) - len(filtered_articles)})')
            return filtered_articles
            
        except Exception as e:
            logger.error(f'Failed to apply filters: {e}')
            return articles  # Return unfiltered on error
    
    @staticmethod
    def toggle_filter(filter_id: int, user: User) -> FilterRule:
        '''Toggle a filter's active state'''
        try:
            with TransactionManager():
                filter_rule = FilterService.get_filter(filter_id, user)
                filter_rule.is_active = not filter_rule.is_active
                filter_rule.save()
                
                status = 'activated' if filter_rule.is_active else 'deactivated'
                logger.info(f'Filter {filter_id} {status}')
                return filter_rule
                
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f'Failed to toggle filter {filter_id}: {e}')
            raise ValidationException(f'Failed to toggle filter: {str(e)}')