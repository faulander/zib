from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, validator
from enum import Enum


class SortField(str, Enum):
    '''Valid sort fields for articles'''
    created_at = 'created_at'
    published_date = 'published_date'
    title = 'title'
    author = 'author'


class SortOrder(str, Enum):
    '''Sort order options'''
    asc = 'asc'
    desc = 'desc'


class ReadStatusFilter(str, Enum):
    '''Read status filter options'''
    all = 'all'
    read = 'read'
    unread = 'unread'
    starred = 'starred'


class FeedInfo(BaseModel):
    '''Feed information in article response'''
    id: int
    title: str
    url: str
    category: Optional[dict] = None


class ReadStatusInfo(BaseModel):
    '''Read status information in article response'''
    is_read: bool = False
    is_starred: bool = False
    is_archived: bool = False
    read_at: Optional[datetime] = None
    starred_at: Optional[datetime] = None


class ArticleResponse(BaseModel):
    '''Article response schema'''
    id: int
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    url: str
    guid: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    tags: List[str] = []
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    feed: FeedInfo
    read_status: ReadStatusInfo
    word_count: Optional[int] = None
    estimated_reading_time: Optional[int] = None

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    '''Article list response with cursor pagination'''
    articles: List[ArticleResponse]
    pagination: dict
    has_more: bool = False
    next_cursor: Optional[int] = None


class ArticleQueryParams(BaseModel):
    '''Query parameters for article list endpoint'''
    limit: int = Field(default=50, ge=1, le=200, description='Number of articles to return')
    since_id: Optional[int] = Field(default=None, description='Return articles older than this ID (for cursor pagination)')
    feed_id: Optional[int] = Field(default=None, description='Filter by feed ID')
    category_id: Optional[int] = Field(default=None, description='Filter by category ID')
    read_status: ReadStatusFilter = Field(default=ReadStatusFilter.all, description='Filter by read status')
    search: Optional[str] = Field(default=None, min_length=2, description='Search in title and content')
    tags: Optional[str] = Field(default=None, description='Filter by tags (comma-separated)')
    author: Optional[str] = Field(default=None, description='Filter by author')
    date_from: Optional[datetime] = Field(default=None, description='Filter articles from this date')
    date_to: Optional[datetime] = Field(default=None, description='Filter articles to this date')
    sort: SortField = Field(default=SortField.published_date, description='Sort field')
    order: SortOrder = Field(default=SortOrder.desc, description='Sort order')

    @validator('date_to')
    def validate_date_range(cls, v, values):
        '''Validate that date_to is after date_from'''
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('date_to must be after date_from')
        return v


class BulkMarkReadRequest(BaseModel):
    '''Request schema for bulk marking articles as read'''
    article_ids: List[int] = Field(..., min_items=1, description='List of article IDs to mark as read')


class BulkOperationResponse(BaseModel):
    '''Response schema for bulk operations'''
    message: str
    updated_count: int


class ArticleStatsResponse(BaseModel):
    '''Article statistics response'''
    total_articles: int
    read_articles: int
    unread_articles: int
    starred_articles: int
    articles_this_week: int
    articles_this_month: int


class MarkArticleRequest(BaseModel):
    '''Request schema for marking article status'''
    # This can be extended in the future for batch operations with additional fields
    pass


class MessageResponse(BaseModel):
    '''Simple message response'''
    message: str


class FilteredCountsResponse(BaseModel):
    '''Filtered article counts response'''
    categories: Dict[int, int]  # category_id -> filtered_count
    feeds: Dict[int, int]       # feed_id -> filtered_count
    total_unread: int