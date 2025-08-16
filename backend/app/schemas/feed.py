from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional
from datetime import datetime
from .common import BaseSchema
from .category import CategoryResponse


class FeedBase(BaseSchema):
    '''Base feed schema with common fields'''
    url: str = Field(..., max_length=500, description='RSS/Atom feed URL')
    title: Optional[str] = Field(None, max_length=200, description='Feed title')
    description: Optional[str] = Field(None, description='Feed description')
    category_id: Optional[int] = Field(None, description='Category ID')
    fetch_interval: int = Field(3600, ge=300, description='Fetch interval in seconds (minimum 5 minutes)')
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        '''Validate URL format'''
        if not v:
            raise ValueError('URL cannot be empty')
        
        # Basic URL validation
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Invalid URL format')
        
        # Additional URL validation can be added here
        try:
            # Use HttpUrl for validation but return string
            HttpUrl(v)
            return v
        except Exception:
            raise ValueError('Invalid URL format')


class FeedCreate(FeedBase):
    '''Schema for creating a new feed'''
    pass


class FeedUpdate(BaseSchema):
    '''Schema for updating a feed'''
    url: Optional[str] = Field(None, max_length=500)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    category_id: Optional[int] = Field(None)
    is_active: Optional[bool] = Field(None)
    fetch_interval: Optional[int] = Field(None, ge=300)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        '''Validate URL format if provided'''
        if v is None:
            return v
        
        if not v:
            raise ValueError('URL cannot be empty')
        
        # Basic URL validation
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Invalid URL format')
        
        try:
            # Use HttpUrl for validation but return string
            HttpUrl(v)
            return v
        except Exception:
            raise ValueError('Invalid URL format')


class FeedResponse(FeedBase):
    '''Schema for feed responses'''
    id: int = Field(..., description='Feed ID')
    is_active: bool = Field(..., description='Whether the feed is active')
    last_fetched: Optional[datetime] = Field(None, description='Last fetch timestamp')
    created_at: datetime = Field(..., description='Creation timestamp')
    updated_at: datetime = Field(..., description='Last update timestamp')
    category: Optional[CategoryResponse] = Field(None, description='Associated category')