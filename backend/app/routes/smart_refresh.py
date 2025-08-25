"""
Smart refresh API endpoints for priority-based feed refresh system
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.models.base import Feed, RefreshMetrics
from app.models.article import User
from app.services.smart_refresh_service import SmartRefreshService, RefreshProgress
from app.core.database import TransactionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/smart-refresh", tags=["smart-refresh"])


# Pydantic models for request/response
class SmartRefreshRequest(BaseModel):
    """Request model for smart refresh"""
    feed_ids: Optional[List[int]] = Field(None, description="Specific feed IDs to refresh (None = all active)")
    batch_size: int = Field(5, ge=1, le=20, description="Number of feeds to process concurrently")
    delay_between_feeds: float = Field(2.0, ge=0.0, le=30.0, description="Delay between batches in seconds")
    recalculate_priorities: bool = Field(False, description="Recalculate priorities before refresh")


class RefreshProgressResponse(BaseModel):
    """Response model for refresh progress"""
    refresh_id: str
    user_id: int
    total_feeds: int
    completed_feeds: int
    successful_refreshes: int
    failed_refreshes: int
    is_active: bool
    cancelled: bool
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: float
    batch_size: int
    priority_algorithm_version: str
    error_summary: Dict
    
    @classmethod
    def from_progress(cls, progress: RefreshProgress) -> "RefreshProgressResponse":
        """Create response from RefreshProgress object"""
        return cls(
            refresh_id=progress.refresh_id,
            user_id=progress.user_id,
            total_feeds=progress.total_feeds,
            completed_feeds=progress.completed_feeds,
            successful_refreshes=progress.successful_refreshes,
            failed_refreshes=progress.failed_refreshes,
            is_active=progress.is_active,
            cancelled=progress.cancelled,
            started_at=progress.started_at,
            completed_at=progress.completed_at,
            duration_seconds=progress.duration_seconds,
            batch_size=progress.batch_size,
            priority_algorithm_version=progress.priority_algorithm_version,
            error_summary=progress.get_error_summary()
        )


class PriorityStatsResponse(BaseModel):
    """Response model for priority statistics"""
    total_feeds: int
    avg_priority: float
    max_priority: float
    min_priority: float
    high_priority_feeds: int
    medium_priority_feeds: int
    low_priority_feeds: int


class FailedFeedResponse(BaseModel):
    """Response model for failed feeds"""
    id: int
    title: str
    url: str
    consecutive_failures: int
    last_checked: Optional[datetime]
    last_successful_refresh: Optional[datetime]
    priority_score: float


class RefreshMetricsResponse(BaseModel):
    """Response model for refresh metrics"""
    id: int
    refresh_started_at: datetime
    feeds_processed: int
    total_duration_seconds: float
    batch_size: int
    priority_algorithm_version: str
    created_at: datetime


# Global service instance (will be properly initialized with user context)
_smart_refresh_services: Dict[int, SmartRefreshService] = {}


def get_smart_refresh_service(user_id: int = 1) -> SmartRefreshService:
    """Get or create smart refresh service for user"""
    if user_id not in _smart_refresh_services:
        try:
            user = User.get_by_id(user_id)
            _smart_refresh_services[user_id] = SmartRefreshService(user)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
    
    return _smart_refresh_services[user_id]


@router.post("/refresh", response_model=RefreshProgressResponse)
async def start_smart_refresh(
    request: SmartRefreshRequest = SmartRefreshRequest(),
    background_tasks: BackgroundTasks = None,
    user_id: int = 1
):
    """
    Start a smart refresh operation with priority-based feed processing
    
    This endpoint initiates a refresh process that:
    1. Orders feeds by priority score (highest first)
    2. Processes feeds in configurable batches
    3. Implements exponential backoff for failures
    4. Tracks progress and provides status updates
    """
    try:
        service = get_smart_refresh_service(user_id)
        
        # Update service configuration
        service.batch_size = request.batch_size
        service.delay_between_feeds = request.delay_between_feeds
        service.recalculate_priorities = request.recalculate_priorities
        
        # Start refresh
        progress = await service.refresh_feeds_by_priority(feed_ids=request.feed_ids)
        
        logger.info(f"Smart refresh completed for user {user_id}: {progress.refresh_id}")
        
        return RefreshProgressResponse.from_progress(progress)
        
    except Exception as e:
        logger.error(f"Smart refresh failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Smart refresh failed: {str(e)}")


@router.get("/refresh/status", response_model=Optional[RefreshProgressResponse])
async def get_current_refresh_status(user_id: int = 1):
    """
    Get the current refresh status for the user
    
    Returns the progress of any active refresh operation, or None if no refresh is running.
    """
    try:
        service = get_smart_refresh_service(user_id)
        progress = service.get_refresh_progress()
        
        if progress:
            return RefreshProgressResponse.from_progress(progress)
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get refresh status for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get refresh status: {str(e)}")


@router.get("/refresh/status/{refresh_id}", response_model=Optional[RefreshProgressResponse])
async def get_refresh_status_by_id(refresh_id: str, user_id: int = 1):
    """
    Get the status of a specific refresh operation by ID
    
    Useful for checking the results of a completed refresh operation.
    """
    try:
        service = get_smart_refresh_service(user_id)
        progress = service.get_refresh_status(refresh_id)
        
        if progress:
            return RefreshProgressResponse.from_progress(progress)
        
        raise HTTPException(status_code=404, detail="Refresh not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get refresh status {refresh_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get refresh status: {str(e)}")


@router.post("/refresh/cancel")
async def cancel_smart_refresh(user_id: int = 1):
    """
    Cancel the current smart refresh operation
    
    Attempts to gracefully cancel any running refresh. Already processed feeds
    will complete, but no new feeds will be started.
    """
    try:
        service = get_smart_refresh_service(user_id)
        
        current_progress = service.get_refresh_progress()
        if not current_progress or not current_progress.is_active:
            raise HTTPException(status_code=400, detail="No active refresh to cancel")
        
        service.cancel_refresh()
        
        return {"message": "Refresh cancellation requested", "refresh_id": current_progress.refresh_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel refresh for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel refresh: {str(e)}")


@router.get("/priority-stats", response_model=PriorityStatsResponse)
async def get_priority_statistics(user_id: int = 1):
    """
    Get statistics about feed priority distribution
    
    Returns information about how feeds are distributed across priority ranges,
    which can help with understanding refresh behavior and optimization.
    """
    try:
        service = get_smart_refresh_service(user_id)
        stats = service.get_priority_stats()
        
        if 'error' in stats:
            raise HTTPException(status_code=500, detail=stats['error'])
        
        return PriorityStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get priority stats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get priority stats: {str(e)}")


@router.get("/failed", response_model=List[FailedFeedResponse])
async def get_failed_feeds(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    user_id: int = 1
):
    """
    Get feeds that have been failing consistently
    
    Returns feeds that have multiple consecutive failures, which may need
    attention or should be temporarily disabled.
    """
    try:
        service = get_smart_refresh_service(user_id)
        failed_feeds = service.get_failed_feeds(days=days)
        
        return [
            FailedFeedResponse(
                id=feed.id,
                title=feed.title or "Untitled Feed",
                url=feed.url,
                consecutive_failures=feed.consecutive_failures or 0,
                last_checked=feed.last_checked,
                last_successful_refresh=feed.last_successful_refresh,
                priority_score=feed.priority_score or 0.0
            )
            for feed in failed_feeds
        ]
        
    except Exception as e:
        logger.error(f"Failed to get failed feeds for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get failed feeds: {str(e)}")


@router.get("/metrics", response_model=List[RefreshMetricsResponse])
async def get_refresh_metrics(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of metrics to return"),
    user_id: int = 1
):
    """
    Get recent refresh performance metrics
    
    Returns historical data about refresh operations for performance analysis
    and optimization.
    """
    try:
        metrics = list(
            RefreshMetrics.select()
            .order_by(RefreshMetrics.created_at.desc())
            .limit(limit)
        )
        
        return [
            RefreshMetricsResponse(
                id=metric.id,
                refresh_started_at=metric.refresh_started_at,
                feeds_processed=metric.feeds_processed,
                total_duration_seconds=metric.total_duration_seconds,
                batch_size=metric.batch_size,
                priority_algorithm_version=metric.priority_algorithm_version,
                created_at=metric.created_at
            )
            for metric in metrics
        ]
        
    except Exception as e:
        logger.error(f"Failed to get refresh metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get refresh metrics: {str(e)}")


@router.post("/refresh/single/{feed_id}")
async def refresh_single_feed(
    feed_id: int,
    max_retries: int = Query(3, ge=0, le=10, description="Maximum retry attempts"),
    user_id: int = 1
):
    """
    Refresh a single feed with retry logic
    
    Useful for manually refreshing specific feeds or retrying failed feeds.
    """
    try:
        # Get the feed
        try:
            feed = Feed.get_by_id(feed_id)
        except Feed.DoesNotExist:
            raise HTTPException(status_code=404, detail="Feed not found")
        
        if not feed.is_active:
            raise HTTPException(status_code=400, detail="Feed is not active")
        
        service = get_smart_refresh_service(user_id)
        success = await service.refresh_single_feed(feed, max_retries=max_retries)
        
        if success:
            return {
                "message": "Feed refreshed successfully",
                "feed_id": feed_id,
                "feed_title": feed.title
            }
        else:
            return {
                "message": "Feed refresh failed",
                "feed_id": feed_id,
                "feed_title": feed.title,
                "consecutive_failures": feed.consecutive_failures
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh single feed {feed_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh feed: {str(e)}")


@router.get("/history", response_model=List[RefreshProgressResponse])
async def get_refresh_history(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of refresh operations to return"),
    user_id: int = 1
):
    """
    Get recent refresh operation history
    
    Returns information about recent smart refresh operations for monitoring
    and debugging purposes.
    """
    try:
        service = get_smart_refresh_service(user_id)
        history = service.get_refresh_history(limit=limit)
        
        return [RefreshProgressResponse.from_progress(progress) for progress in history]
        
    except Exception as e:
        logger.error(f"Failed to get refresh history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get refresh history: {str(e)}")


# Add health check endpoint
@router.get("/health")
async def smart_refresh_health_check():
    """Health check for smart refresh system"""
    try:
        # Test database connection
        feed_count = Feed.select().where(Feed.is_active == True).count()
        
        # Test basic functionality
        test_user = User.select().first()
        if test_user:
            service = SmartRefreshService(test_user)
            stats = service.get_priority_stats()
            
            return {
                "status": "healthy",
                "active_feeds": feed_count,
                "priority_stats": stats,
                "timestamp": datetime.now()
            }
        else:
            return {
                "status": "no_users", 
                "active_feeds": feed_count,
                "timestamp": datetime.now()
            }
            
    except Exception as e:
        logger.error(f"Smart refresh health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }