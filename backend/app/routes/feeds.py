from fastapi import APIRouter, Query, Path, status, HTTPException
from typing import Optional
from app.schemas.feed import FeedCreate, FeedUpdate, FeedResponse
from app.schemas.common import SuccessResponse, PaginatedResponse
from app.schemas.feed_health import (
    FeedCheckSessionResponse, FeedCheckStatusResponse, BrokenFeedsResponse,
    BulkDeleteRequest, BulkDeleteResponse, FeedCheckHistoryResponse
)
from app.services.feed_service import FeedService
from app.services.feed_health_service import feed_health_service
from app.models.base import Category
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


# Feed Health Endpoints

@router.post('/check-category/{category_id}', response_model=FeedCheckSessionResponse)
async def check_category_feeds(category_id: int = Path(..., description='Category ID')):
    """Initiate feed accessibility checking for all feeds in a category"""
    logger.info(f'Starting feed check for category: {category_id}')
    
    try:
        # Verify category exists
        try:
            category = Category.get_by_id(category_id)
        except Category.DoesNotExist:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Start feed checking
        session_id = await feed_health_service.check_category_feeds(category_id)
        
        if not session_id:
            raise HTTPException(status_code=400, detail="No active feeds found in category")
        
        # Get session info for response
        session_status = feed_health_service.get_session_status(session_id)
        total_feeds = session_status['progress']['total'] if session_status else 0
        
        return FeedCheckSessionResponse(
            session_id=session_id,
            message="Feed checking started",
            total_feeds=total_feeds,
            estimated_duration=f"{total_feeds * 2} seconds"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error starting feed check for category {category_id}: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/check-status/{session_id}', response_model=FeedCheckStatusResponse)
async def get_check_status(session_id: str = Path(..., description='Session ID')):
    """Get progress status of ongoing feed check operation"""
    logger.debug(f'Getting check status for session: {session_id}')
    
    session_status = feed_health_service.get_session_status(session_id)
    
    if not session_status:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    return FeedCheckStatusResponse(**session_status)


@router.get('/broken/{category_id}', response_model=BrokenFeedsResponse)
async def get_broken_feeds(
    category_id: int = Path(..., description='Category ID'),
    days: int = Query(7, ge=1, le=365, description='Days threshold for broken feeds')
):
    """Get list of feeds that have been inaccessible for specified number of days"""
    logger.info(f'Getting broken feeds for category {category_id} (>{days} days)')
    
    try:
        # Verify category exists
        try:
            category = Category.get_by_id(category_id)
        except Category.DoesNotExist:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Get broken feeds
        broken_feeds = feed_health_service.get_broken_feeds(category_id, days)
        
        return BrokenFeedsResponse(
            broken_feeds=broken_feeds,
            total_broken=len(broken_feeds),
            category_name=category.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error getting broken feeds for category {category_id}: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/bulk-delete', response_model=BulkDeleteResponse)
async def bulk_delete_feeds(request: BulkDeleteRequest):
    """Delete multiple feeds in a single operation"""
    logger.info(f'Bulk deleting {len(request.feed_ids)} feeds')
    
    try:
        result = feed_health_service.bulk_delete_feeds(request.feed_ids)
        return BulkDeleteResponse(**result)
        
    except Exception as e:
        logger.error(f'Error in bulk delete operation: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{feed_id}/check-history', response_model=FeedCheckHistoryResponse)
async def get_feed_check_history(
    feed_id: int = Path(..., description='Feed ID'),
    limit: int = Query(20, ge=1, le=100, description='Number of history entries to return')
):
    """Get detailed check history for a specific feed"""
    logger.info(f'Getting check history for feed {feed_id}')
    
    try:
        history = feed_health_service.get_feed_check_history(feed_id, limit)
        
        if 'error' in history:
            raise HTTPException(status_code=404, detail=history['error'])
        
        return FeedCheckHistoryResponse(**history)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error getting feed check history for {feed_id}: {e}')
        raise HTTPException(status_code=500, detail=str(e))