from fastapi import APIRouter, Path, Query, status
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.common import SuccessResponse, PaginatedResponse
from app.services.category_service import CategoryService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix='/categories', tags=['categories'])


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=CategoryResponse)
async def create_category(category_data: CategoryCreate):
    '''Create a new category'''
    logger.info(f'Creating category: {category_data.name}')
    return CategoryService.create_category(category_data)


@router.get('/{category_id}', response_model=CategoryResponse)
async def get_category(
    category_id: int = Path(..., description='Category ID'),
    include_feeds: bool = Query(False, description='Include associated feeds')
):
    '''Get a specific category by ID'''
    logger.info(f'Retrieving category: {category_id}')
    return CategoryService.get_category_by_id(category_id, include_feeds=include_feeds)


@router.put('/{category_id}', response_model=CategoryResponse)
async def update_category(
    category_data: CategoryUpdate,
    category_id: int = Path(..., description='Category ID')
):
    '''Update an existing category'''
    logger.info(f'Updating category: {category_id}')
    return CategoryService.update_category(category_id, category_data)


@router.delete('/{category_id}', response_model=SuccessResponse)
async def delete_category(category_id: int = Path(..., description='Category ID')):
    '''Delete a category'''
    logger.info(f'Deleting category: {category_id}')
    result = CategoryService.delete_category(category_id)
    return SuccessResponse(
        message=result['message'],
        data={'category_id': result['category_id'], 'name': result['name']}
    )


@router.get('/', response_model=PaginatedResponse)
async def list_categories(
    page: int = Query(1, ge=1, description='Page number'),
    page_size: int = Query(10, ge=1, le=1000, description='Items per page'),
    include_feeds: bool = Query(False, description='Include associated feeds')
):
    '''List categories with pagination'''
    logger.info(f'Listing categories - page {page}, size {page_size}')
    return CategoryService.list_categories(page=page, page_size=page_size, include_feeds=include_feeds)