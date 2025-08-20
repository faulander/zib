import asyncio
import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

import httpx
from app.models.base import Feed, FeedCheckLog
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FeedCheckResult:
    """Result of a feed accessibility check"""
    success: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None


class FeedCheckSession:
    """Tracks progress of feed checking for a category"""
    
    def __init__(self, session_id: str, category_id: int, feed_ids: List[int]):
        self.session_id = session_id
        self.category_id = category_id
        self.feed_ids = feed_ids
        self.completed = 0
        self.status = "pending"
        self.results = {"accessible": 0, "inaccessible": 0}
        self.current_feed = None
        self.errors = []
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start the feed checking session"""
        self.status = "running"
        self.start_time = datetime.now()
        logger.info(f"Started feed check session {self.session_id} for category {self.category_id}")
    
    def update_progress(self, accessible: bool, feed_title: str = None):
        """Update progress after checking a feed"""
        self.completed += 1
        
        if accessible:
            self.results["accessible"] += 1
        else:
            self.results["inaccessible"] += 1
        
        if feed_title:
            self.current_feed = feed_title
        
        # Check if complete
        if self.completed >= len(self.feed_ids):
            self.complete()
    
    def complete(self):
        """Mark session as completed"""
        self.status = "completed"
        self.end_time = datetime.now()
        self.current_feed = None
        
        duration = self.end_time - self.start_time if self.start_time else None
        logger.info(f"Completed feed check session {self.session_id}. "
                   f"Results: {self.results['accessible']} accessible, "
                   f"{self.results['inaccessible']} inaccessible. "
                   f"Duration: {duration}")
    
    def add_error(self, error_message: str):
        """Add an error message to the session"""
        self.errors.append(error_message)
        logger.warning(f"Session {self.session_id} error: {error_message}")
    
    def is_complete(self) -> bool:
        """Check if session is complete"""
        return self.completed >= len(self.feed_ids)
    
    def get_progress_percentage(self) -> int:
        """Get progress as percentage"""
        if not self.feed_ids:
            return 100
        return min(100, int((self.completed / len(self.feed_ids)) * 100))
    
    def to_dict(self) -> dict:
        """Convert session to dictionary for API response"""
        # Calculate pending feeds
        pending = len(self.feed_ids) - self.completed
        results_with_pending = self.results.copy()
        results_with_pending["pending"] = pending
        
        return {
            "session_id": self.session_id,
            "status": self.status,
            "progress": {
                "completed": self.completed,
                "total": len(self.feed_ids),
                "current_feed": self.current_feed,
                "percentage": self.get_progress_percentage(),
                "categoryId": self.category_id
            },
            "results": results_with_pending,
            "errors": self.errors.copy()
        }


class FeedHealthService:
    """Service for checking feed health and managing accessibility"""
    
    def __init__(self, timeout: int = 10, user_agent: str = None):
        self.timeout = timeout
        self.user_agent = user_agent or "Zib RSS Reader/1.0"
        self.active_sessions: Dict[str, FeedCheckSession] = {}
    
    async def check_feed_accessibility(self, feed_url: str) -> FeedCheckResult:
        """Check if a feed URL is accessible"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.head(
                    feed_url,
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True
                )
                
                response_time = int((time.time() - start_time) * 1000)
                
                # Consider 2xx and 3xx status codes as successful
                success = response.status_code < 400
                
                return FeedCheckResult(
                    success=success,
                    status_code=response.status_code,
                    response_time_ms=response_time
                )
                
        except httpx.TimeoutException:
            response_time = int((time.time() - start_time) * 1000)
            return FeedCheckResult(
                success=False,
                error_message="Request timed out",
                response_time_ms=response_time
            )
            
        except httpx.ConnectError as e:
            response_time = int((time.time() - start_time) * 1000)
            error_msg = str(e).lower()
            
            if "ssl" in error_msg or "certificate" in error_msg:
                error_message = "SSL certificate verification failed"
            else:
                error_message = "Connection failed"
                
            return FeedCheckResult(
                success=False,
                error_message=error_message,
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            return FeedCheckResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                response_time_ms=response_time
            )
    
    def update_feed_status(self, feed: Feed, check_result: FeedCheckResult):
        """Update feed accessibility status based on check result"""
        feed.last_checked = datetime.now()
        
        if check_result.success:
            # Reset failures on success
            feed.accessible = True
            feed.consecutive_failures = 0
        else:
            # Increment failures on failure
            feed.accessible = False
            feed.consecutive_failures += 1
        
        feed.save()
        
        logger.debug(f"Updated feed {feed.id} ({feed.title}): "
                    f"accessible={feed.accessible}, "
                    f"consecutive_failures={feed.consecutive_failures}")
    
    def log_feed_check_result(self, feed: Feed, check_result: FeedCheckResult):
        """Log the feed check result to database"""
        FeedCheckLog.create(
            feed=feed,
            checked_at=datetime.now(),
            status_code=check_result.status_code,
            error_message=check_result.error_message,
            response_time_ms=check_result.response_time_ms,
            is_success=check_result.success,
            user_agent=self.user_agent
        )
    
    async def check_and_update_feed(self, feed: Feed, session: FeedCheckSession = None):
        """Check a single feed and update its status"""
        try:
            check_result = await self.check_feed_accessibility(feed.url)
            
            # Update feed status
            self.update_feed_status(feed, check_result)
            
            # Log the result
            self.log_feed_check_result(feed, check_result)
            
            # Update session progress if provided
            if session:
                session.update_progress(check_result.success, feed.title)
            
            logger.info(f"Checked feed {feed.id} ({feed.title}): "
                       f"{'✓' if check_result.success else '✗'} "
                       f"{check_result.status_code or check_result.error_message}")
            
            return check_result
            
        except Exception as e:
            error_msg = f"Failed to check feed {feed.id}: {str(e)}"
            logger.error(error_msg)
            
            if session:
                session.add_error(error_msg)
                session.update_progress(False, feed.title)
            
            raise
    
    async def check_category_feeds(self, category_id: int) -> str:
        """Start checking all feeds in a category (async)"""
        # Get all accessible feeds in category
        feeds = list(Feed.select().where(
            (Feed.category_id == category_id) & 
            (Feed.is_active == True)
        ))
        
        if not feeds:
            logger.warning(f"No active feeds found in category {category_id}")
            return None
        
        # Create session
        session_id = str(uuid.uuid4())
        feed_ids = [f.id for f in feeds]
        session = FeedCheckSession(session_id, category_id, feed_ids)
        
        # Store session for progress tracking
        self.active_sessions[session_id] = session
        
        # Start checking feeds in background
        asyncio.create_task(self._check_feeds_background(feeds, session))
        
        return session_id
    
    async def _check_feeds_background(self, feeds: List[Feed], session: FeedCheckSession):
        """Background task to check all feeds in a session"""
        session.start()
        
        try:
            # Create tasks for concurrent checking
            tasks = [self.check_and_update_feed(feed, session) for feed in feeds]
            
            # Wait for all checks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Feed checking session {session.session_id} failed: {e}")
            session.add_error(f"Session failed: {str(e)}")
        
        finally:
            if not session.is_complete():
                session.complete()
            
            # Schedule cleanup of completed session (after 5 minutes)
            asyncio.create_task(self._cleanup_session(session.session_id, delay=300))
    
    async def _cleanup_session(self, session_id: str, delay: int = 300):
        """Clean up completed session after delay"""
        await asyncio.sleep(delay)
        if session_id in self.active_sessions:
            logger.info(f"Cleaning up completed session {session_id}")
            del self.active_sessions[session_id]
    
    def get_session_status(self, session_id: str) -> Optional[dict]:
        """Get status of an active session"""
        session = self.active_sessions.get(session_id)
        return session.to_dict() if session else None
    
    def get_broken_feeds(self, category_id: int, days_threshold: int = 7) -> List[dict]:
        """Get feeds that have been broken for the specified number of days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        broken_feeds = Feed.select().where(
            (Feed.category_id == category_id) &
            (Feed.accessible == False) &
            ((Feed.last_checked.is_null()) | (Feed.last_checked <= cutoff_date))
        ).order_by(Feed.last_checked.asc())
        
        result = []
        for feed in broken_feeds:
            # Get recent error history
            recent_errors = (FeedCheckLog
                           .select()
                           .where((FeedCheckLog.feed == feed) & (FeedCheckLog.is_success == False))
                           .order_by(FeedCheckLog.checked_at.desc())
                           .limit(3))
            
            # Find last successful check
            last_success = (FeedCheckLog
                          .select()
                          .where((FeedCheckLog.feed == feed) & (FeedCheckLog.is_success == True))
                          .order_by(FeedCheckLog.checked_at.desc())
                          .first())
            
            result.append({
                "id": feed.id,
                "title": feed.title,
                "url": feed.url,
                "last_checked": feed.last_checked,
                "consecutive_failures": feed.consecutive_failures,
                "last_success": last_success.checked_at if last_success else None,
                "recent_errors": [
                    {
                        "checked_at": err.checked_at,
                        "error_message": err.error_message,
                        "status_code": err.status_code
                    }
                    for err in recent_errors
                ]
            })
        
        return result
    
    def bulk_delete_feeds(self, feed_ids: List[int]) -> dict:
        """Delete multiple feeds and return results"""
        results = {
            "deleted_count": 0,
            "failed_deletions": []
        }
        
        for feed_id in feed_ids:
            try:
                feed = Feed.get_by_id(feed_id)
                feed.delete_instance(recursive=True)  # Cascade delete related records
                results["deleted_count"] += 1
                logger.info(f"Deleted feed {feed_id}: {feed.title}")
                
            except Feed.DoesNotExist:
                results["failed_deletions"].append({
                    "feed_id": feed_id,
                    "error": "Feed not found"
                })
            except Exception as e:
                results["failed_deletions"].append({
                    "feed_id": feed_id,
                    "error": str(e)
                })
                logger.error(f"Failed to delete feed {feed_id}: {e}")
        
        total_requested = len(feed_ids)
        results["message"] = f"Successfully deleted {results['deleted_count']} of {total_requested} feeds"
        
        return results
    
    def get_feed_check_history(self, feed_id: int, limit: int = 20) -> dict:
        """Get check history for a specific feed"""
        try:
            feed = Feed.get_by_id(feed_id)
        except Feed.DoesNotExist:
            return {"error": "Feed not found"}
        
        # Get check history
        history = (FeedCheckLog
                  .select()
                  .where(FeedCheckLog.feed == feed)
                  .order_by(FeedCheckLog.checked_at.desc())
                  .limit(limit))
        
        # Calculate statistics
        total_checks = FeedCheckLog.select().where(FeedCheckLog.feed == feed).count()
        successful_checks = FeedCheckLog.select().where(
            (FeedCheckLog.feed == feed) & (FeedCheckLog.is_success == True)
        ).count()
        
        success_rate = successful_checks / total_checks if total_checks > 0 else 0.0
        
        return {
            "feed_id": feed.id,
            "feed_title": feed.title,
            "check_history": [
                {
                    "checked_at": log.checked_at,
                    "is_success": log.is_success,
                    "status_code": log.status_code,
                    "error_message": log.error_message,
                    "response_time_ms": log.response_time_ms
                }
                for log in history
            ],
            "total_checks": total_checks,
            "success_rate": round(success_rate, 3)
        }


# Global service instance
feed_health_service = FeedHealthService()