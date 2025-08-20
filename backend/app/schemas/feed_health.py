from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class FeedCheckSessionResponse(BaseModel):
    """Response schema for feed check session initiation"""
    session_id: str
    message: str
    total_feeds: int
    estimated_duration: str


class FeedCheckProgressResponse(BaseModel):
    """Response schema for feed check progress"""
    completed: int
    total: int
    current_feed: Optional[str] = None
    percentage: int
    categoryId: int


class FeedCheckResultsResponse(BaseModel):
    """Response schema for feed check results"""
    accessible: int
    inaccessible: int
    pending: int


class FeedCheckStatusResponse(BaseModel):
    """Response schema for feed check status"""
    session_id: str
    status: str
    progress: FeedCheckProgressResponse
    results: FeedCheckResultsResponse
    errors: List[str] = Field(default_factory=list)


class RecentErrorResponse(BaseModel):
    """Response schema for recent feed errors"""
    checked_at: datetime
    error_message: Optional[str] = None
    status_code: Optional[int] = None


class BrokenFeedResponse(BaseModel):
    """Response schema for broken feed information"""
    id: int
    title: str
    url: str
    last_checked: Optional[datetime] = None
    consecutive_failures: int
    last_success: Optional[datetime] = None
    recent_errors: List[RecentErrorResponse] = Field(default_factory=list)


class BrokenFeedsResponse(BaseModel):
    """Response schema for broken feeds list"""
    broken_feeds: List[BrokenFeedResponse]
    total_broken: int
    category_name: str


class BulkDeleteRequest(BaseModel):
    """Request schema for bulk feed deletion"""
    feed_ids: List[int] = Field(..., min_items=1, description="List of feed IDs to delete")


class BulkDeleteFailure(BaseModel):
    """Response schema for bulk delete failures"""
    feed_id: int
    error: str


class BulkDeleteResponse(BaseModel):
    """Response schema for bulk delete operation"""
    deleted_count: int
    failed_deletions: List[BulkDeleteFailure] = Field(default_factory=list)
    message: str


class FeedCheckHistoryEntry(BaseModel):
    """Response schema for feed check history entry"""
    checked_at: datetime
    is_success: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None


class FeedCheckHistoryResponse(BaseModel):
    """Response schema for feed check history"""
    feed_id: int
    feed_title: str
    check_history: List[FeedCheckHistoryEntry]
    total_checks: int
    success_rate: float