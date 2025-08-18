from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.models.article import User
from app.services.filter_service import FilterService
from app.core.exceptions import ValidationException

router = APIRouter(prefix='/api/filters', tags=['filters'])


# Schemas
class FilterRequest(BaseModel):
    '''Request model for creating/updating filters'''
    name: str = Field(..., min_length=1, max_length=100)
    filter_type: str = Field(default='title_contains')
    filter_value: str = Field(..., min_length=1, max_length=2000)
    category_id: Optional[int] = None
    feed_id: Optional[int] = None
    is_active: bool = True
    case_sensitive: bool = False


class FilterResponse(BaseModel):
    '''Response model for filter rules'''
    id: int
    name: str
    filter_type: str
    filter_value: str
    category_id: Optional[int]
    category_name: Optional[str]
    feed_id: Optional[int]
    is_active: bool
    case_sensitive: bool
    created_at: str
    updated_at: str


@router.get('', response_model=List[FilterResponse])
async def get_filters(
    active_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    '''Get all filters for the current user'''
    try:
        filters = FilterService.get_user_filters(current_user, active_only)
        
        return [
            FilterResponse(
                id=f.id,
                name=f.name,
                filter_type=f.filter_type,
                filter_value=f.filter_value,
                category_id=f.category_id if f.category else None,
                category_name=f.category.name if f.category else None,
                feed_id=f.feed_id,
                is_active=f.is_active,
                case_sensitive=f.case_sensitive,
                created_at=f.created_at.isoformat(),
                updated_at=f.updated_at.isoformat()
            )
            for f in filters
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to get filters: {str(e)}'
        )


@router.get('/{filter_id}', response_model=FilterResponse)
async def get_filter(
    filter_id: int,
    current_user: User = Depends(get_current_user)
):
    '''Get a specific filter'''
    try:
        filter_rule = FilterService.get_filter(filter_id, current_user)
        
        return FilterResponse(
            id=filter_rule.id,
            name=filter_rule.name,
            filter_type=filter_rule.filter_type,
            filter_value=filter_rule.filter_value,
            category_id=filter_rule.category_id if filter_rule.category else None,
            category_name=filter_rule.category.name if filter_rule.category else None,
            feed_id=filter_rule.feed_id,
            is_active=filter_rule.is_active,
            case_sensitive=filter_rule.case_sensitive,
            created_at=filter_rule.created_at.isoformat(),
            updated_at=filter_rule.updated_at.isoformat()
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to get filter: {str(e)}'
        )


@router.post('', response_model=FilterResponse)
async def create_filter(
    filter_data: FilterRequest,
    current_user: User = Depends(get_current_user)
):
    '''Create a new filter rule'''
    try:
        filter_rule = FilterService.create_filter(
            current_user,
            filter_data.model_dump()
        )
        
        return FilterResponse(
            id=filter_rule.id,
            name=filter_rule.name,
            filter_type=filter_rule.filter_type,
            filter_value=filter_rule.filter_value,
            category_id=filter_rule.category_id if filter_rule.category else None,
            category_name=filter_rule.category.name if filter_rule.category else None,
            feed_id=filter_rule.feed_id,
            is_active=filter_rule.is_active,
            case_sensitive=filter_rule.case_sensitive,
            created_at=filter_rule.created_at.isoformat(),
            updated_at=filter_rule.updated_at.isoformat()
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to create filter: {str(e)}'
        )


@router.put('/{filter_id}', response_model=FilterResponse)
async def update_filter(
    filter_id: int,
    filter_data: FilterRequest,
    current_user: User = Depends(get_current_user)
):
    '''Update a filter rule'''
    try:
        filter_rule = FilterService.update_filter(
            filter_id,
            current_user,
            filter_data.model_dump()
        )
        
        return FilterResponse(
            id=filter_rule.id,
            name=filter_rule.name,
            filter_type=filter_rule.filter_type,
            filter_value=filter_rule.filter_value,
            category_id=filter_rule.category_id if filter_rule.category else None,
            category_name=filter_rule.category.name if filter_rule.category else None,
            feed_id=filter_rule.feed_id,
            is_active=filter_rule.is_active,
            case_sensitive=filter_rule.case_sensitive,
            created_at=filter_rule.created_at.isoformat(),
            updated_at=filter_rule.updated_at.isoformat()
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to update filter: {str(e)}'
        )


@router.delete('/{filter_id}')
async def delete_filter(
    filter_id: int,
    current_user: User = Depends(get_current_user)
):
    '''Delete a filter rule'''
    try:
        FilterService.delete_filter(filter_id, current_user)
        return {'message': f'Filter {filter_id} deleted successfully'}
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to delete filter: {str(e)}'
        )


@router.post('/{filter_id}/toggle')
async def toggle_filter(
    filter_id: int,
    current_user: User = Depends(get_current_user)
):
    '''Toggle a filter's active state'''
    try:
        filter_rule = FilterService.toggle_filter(filter_id, current_user)
        
        return {
            'message': f'Filter {filter_id} {"activated" if filter_rule.is_active else "deactivated"}',
            'is_active': filter_rule.is_active
        }
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to toggle filter: {str(e)}'
        )