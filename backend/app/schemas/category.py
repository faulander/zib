from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from .common import BaseSchema


class CategoryBase(BaseSchema):
    '''Base category schema with common fields'''
    name: str = Field(..., min_length=1, max_length=100, description='Category name')
    description: Optional[str] = Field(None, max_length=500, description='Category description')
    color: Optional[str] = Field(None, description='Hex color code for category')
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        '''Validate hex color format'''
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError('Color must be a string')
        
        # Remove # if present
        color = v.lstrip('#')
        
        # Check if it's a valid hex color (3 or 6 characters)
        if len(color) not in [3, 6]:
            raise ValueError('Invalid hex color format')
        
        try:
            int(color, 16)
        except ValueError:
            raise ValueError('Invalid hex color format')
        
        # Return with # prefix
        return f'#{color.upper()}'


class CategoryCreate(CategoryBase):
    '''Schema for creating a new category'''
    pass


class CategoryUpdate(BaseSchema):
    '''Schema for updating a category'''
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None)
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        '''Validate hex color format'''
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError('Color must be a string')
        
        # Remove # if present
        color = v.lstrip('#')
        
        # Check if it's a valid hex color (3 or 6 characters)
        if len(color) not in [3, 6]:
            raise ValueError('Invalid hex color format')
        
        try:
            int(color, 16)
        except ValueError:
            raise ValueError('Invalid hex color format')
        
        # Return with # prefix
        return f'#{color.upper()}'


class CategoryResponse(CategoryBase):
    '''Schema for category responses'''
    id: int = Field(..., description='Category ID')
    created_at: datetime = Field(..., description='Creation timestamp')
    updated_at: datetime = Field(..., description='Last update timestamp')