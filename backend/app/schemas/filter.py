from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from .common import BaseSchema


class FilterBase(BaseSchema):
    '''Base filter schema with common fields'''
    name: str = Field(..., min_length=1, max_length=100, description='Filter name')
    type: str = Field(..., max_length=50, description='Filter type (keyword, regex, category, etc.)')
    criteria: Dict[str, Any] = Field(..., description='Filter criteria as JSON object')
    
    @field_validator('criteria')
    @classmethod
    def validate_criteria(cls, v):
        '''Validate filter criteria'''
        if not isinstance(v, dict):
            raise ValueError('Criteria must be a dictionary')
        
        # Basic validation - ensure it's not empty
        if not v:
            raise ValueError('Criteria cannot be empty')
        
        # Additional validation based on filter type can be added here
        return v


class FilterCreate(FilterBase):
    '''Schema for creating a new filter'''
    pass


class FilterUpdate(BaseSchema):
    '''Schema for updating a filter'''
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, max_length=50)
    criteria: Optional[Dict[str, Any]] = Field(None)
    is_active: Optional[bool] = Field(None)
    
    @field_validator('criteria')
    @classmethod
    def validate_criteria(cls, v):
        '''Validate filter criteria if provided'''
        if v is None:
            return v
        
        if not isinstance(v, dict):
            raise ValueError('Criteria must be a dictionary')
        
        if not v:
            raise ValueError('Criteria cannot be empty')
        
        return v


class FilterResponse(FilterBase):
    '''Schema for filter responses'''
    id: int = Field(..., description='Filter ID')
    is_active: bool = Field(..., description='Whether the filter is active')
    created_at: datetime = Field(..., description='Creation timestamp')
    updated_at: datetime = Field(..., description='Last update timestamp')