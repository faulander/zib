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


@router.get('/', response_model=PaginatedResponse)
async def list_feeds(
    page: int = Query(1, ge=1, description='Page number'),
    page_size: int = Query(10, ge=1, le=100, description='Items per page'),
    category_id: Optional[int] = Query(None, description='Filter by category ID'),
    is_active: Optional[bool] = Query(None, description='Filter by active status'),
    include_category: bool = Query(False, description='Include category information')
):
    '''List feeds with pagination and filtering'''
    logger.info(f'Listing feeds: page={page}, page_size={page_size}')
    return FeedService.list_feeds(
        page=page,
        page_size=page_size,
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