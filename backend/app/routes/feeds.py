from fastapi import APIRouter, Query, Path, status
from typing import Optional
from app.schemas.feed import FeedCreate, FeedUpdate, FeedResponse
from app.schemas.common import SuccessResponse, PaginatedResponse
from app.services.feed_service import FeedService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix='/feeds', tags=['feeds'])


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=FeedResponse)
async def create_feed(feed_data: FeedCreate):
    '''Create a new RSS feed'''
    logger.info(f'Creating feed: {feed_data.url}')
    return FeedService.create_feed(feed_data)


@router.get('/{feed_id}', response_model=FeedResponse)
async def get_feed(
    feed_id: int = Path(..., description='Feed ID'),
    include_category: bool = Query(False, description='Include category information')
):
    '''Get a specific feed by ID'''
    logger.info(f'Retrieving feed: {feed_id}')
    return FeedService.get_feed_by_id(feed_id, include_category=include_category)


@router.put('/{feed_id}', response_model=FeedResponse)
async def update_feed(
    feed_data: FeedUpdate,
    feed_id: int = Path(..., description='Feed ID')
):
    '''Update an existing feed'''
    logger.info(f'Updating feed: {feed_id}')
    return FeedService.update_feed(feed_id, feed_data)


@router.delete('/{feed_id}', response_model=SuccessResponse)
async def delete_feed(feed_id: int = Path(..., description='Feed ID')):
    '''Delete a feed'''
    logger.info(f'Deleting feed: {feed_id}')
    result = FeedService.delete_feed(feed_id)
    return SuccessResponse(
        message=result['message'],
        data={'feed_id': result['feed_id'], 'url': result['url']}
    )


@router.get('/')
async def list_feeds(
    category_id: Optional[int] = Query(None, description='Filter by category ID'),
    is_active: Optional[bool] = Query(None, description='Filter by active status'),
    include_category: bool = Query(False, description='Include category information')
):
    '''List all feeds with filtering'''
    logger.info('Listing all feeds')
    return FeedService.list_all_feeds(
        category_id=category_id,
        is_active=is_active,
        include_category=include_category
    )


@router.patch('/{feed_id}/status', response_model=FeedResponse)
async def update_feed_status(
    feed_id: int = Path(..., description='Feed ID'),
    is_active: bool = Query(..., description='Active status')
):
    '''Update feed active status'''
    logger.info(f'Updating feed status: {feed_id} -> active={is_active}')
    return FeedService.update_feed_status(feed_id, is_active)


@router.get('/category/{category_id}', response_model=list[FeedResponse])
async def get_feeds_by_category(category_id: int = Path(..., description='Category ID')):
    '''Get all feeds in a specific category'''
    logger.info(f'Getting feeds by category: {category_id}')
    return FeedService.get_feeds_by_category(category_id)


@router.post('/{feed_id}/refresh', response_model=SuccessResponse)
async def refresh_feed(feed_id: int = Path(..., description='Feed ID')):
    '''Manually refresh a specific feed to fetch new articles'''
    logger.info(f'Manually refreshing feed: {feed_id}')
    from app.services.feed_fetcher import feed_fetcher
    from app.models.base import Feed
    
    try:
        # Get the feed
        feed = Feed.get_by_id(feed_id)
        
        # Update the feed
        result = await feed_fetcher.update_feed(feed, force=True)
        
        if result.success:
            return SuccessResponse(
                message=f'Feed refreshed successfully',
                data={
                    'feed_id': feed_id,
                    'articles_added': result.articles_added,
                    'articles_updated': result.articles_updated,
                    'processing_time': result.processing_time
                }
            )
        else:
            return SuccessResponse(
                message=f'Feed refresh failed: {result.error_message}',
                data={'feed_id': feed_id, 'error': result.error_message}
            )
            
    except Exception as e:
        logger.error(f'Error refreshing feed {feed_id}: {e}')
        return SuccessResponse(
            message=f'Feed refresh failed: {str(e)}',
            data={'feed_id': feed_id, 'error': str(e)}
        )


@router.post('/refresh-all', response_model=SuccessResponse)
async def refresh_all_feeds():
    '''Refresh all active feeds to fetch new articles'''
    logger.info('Manually refreshing all feeds')
    from app.services.feed_fetcher import feed_fetcher
    from app.models.base import Feed
    
    try:
        # Get all active feeds
        feeds = list(Feed.select().where(Feed.is_active == True))
        
        if not feeds:
            return SuccessResponse(
                message='No active feeds to refresh',
                data={'total_feeds': 0}
            )
        
        # Update all feeds
        results = await feed_fetcher.update_multiple_feeds(feeds, force=True, max_concurrent=5)
        
        # Calculate summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_articles_added = sum(r.articles_added for r in results if r.success)
        
        return SuccessResponse(
            message=f'Refreshed {len(feeds)} feeds',
            data={
                'total_feeds': len(feeds),
                'successful': successful,
                'failed': failed,
                'articles_added': total_articles_added
            }
        )
        
    except Exception as e:
        logger.error(f'Error refreshing all feeds: {e}')
        return SuccessResponse(
            message=f'Feed refresh failed: {str(e)}',
            data={'error': str(e)}
        )