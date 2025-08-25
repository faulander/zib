"""
SmartRefreshService - Priority-based sequential feed refresh system

Processes feeds in priority order with configurable batching, error handling,
and progress tracking for optimal refresh performance.
"""

import logging
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

import pendulum

from app.models.base import Feed, RefreshMetrics
from app.models.article import User
from app.services.priority_calculator import FeedPriorityCalculator
from app.core.database import TransactionManager

logger = logging.getLogger(__name__)


@dataclass
class RefreshProgress:
    """Track progress of a smart refresh operation"""
    
    refresh_id: str
    user_id: int
    total_feeds: int
    
    # Progress tracking
    completed_feeds: int = 0
    successful_refreshes: int = 0
    failed_refreshes: int = 0
    
    # Status flags
    is_active: bool = False
    cancelled: bool = False
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Error tracking
    errors: Dict[int, Dict] = field(default_factory=dict)  # feed_id -> error info
    
    # Configuration
    batch_size: int = 5
    priority_algorithm_version: str = 'v1.0'
    
    def start(self):
        """Mark refresh as started"""
        self.is_active = True
        self.started_at = datetime.now()
        logger.info(f"Smart refresh {self.refresh_id} started for user {self.user_id} ({self.total_feeds} feeds)")
    
    def complete(self):
        """Mark refresh as completed"""
        self.is_active = False
        self.completed_at = datetime.now()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        
        logger.info(f"Smart refresh {self.refresh_id} completed: {self.successful_refreshes} successful, "
                   f"{self.failed_refreshes} failed, {self.duration_seconds:.1f}s")
    
    def cancel(self):
        """Mark refresh as cancelled"""
        self.is_active = False
        self.cancelled = True
        self.completed_at = datetime.now()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        
        logger.info(f"Smart refresh {self.refresh_id} cancelled after {self.duration_seconds:.1f}s")
    
    def update_progress(self, completed: int, successful: int, failed: int):
        """Update refresh progress counters"""
        self.completed_feeds = completed
        self.successful_refreshes = successful
        self.failed_refreshes = failed
    
    def add_error(self, feed_id: int, error_message: str):
        """Add error information for a feed"""
        if feed_id not in self.errors:
            self.errors[feed_id] = {
                'count': 0,
                'first_error': error_message,
                'last_error': error_message,
                'timestamps': []
            }
        
        self.errors[feed_id]['count'] += 1
        self.errors[feed_id]['last_error'] = error_message
        self.errors[feed_id]['timestamps'].append(datetime.now())
        
        logger.debug(f"Error recorded for feed {feed_id}: {error_message}")
    
    def get_error_summary(self) -> Dict:
        """Get summary of errors encountered"""
        return {
            'total_errors': len(self.errors),
            'feeds_with_errors': list(self.errors.keys()),
            'error_details': {
                feed_id: {
                    'count': info['count'],
                    'last_error': info['last_error']
                }
                for feed_id, info in self.errors.items()
            }
        }


class SmartRefreshService:
    """Smart refresh service with priority-based sequential processing"""
    
    def __init__(self, user: User, batch_size: int = 5, delay_between_feeds: float = 2.0,
                 max_retries: int = 3, recalculate_priorities: bool = False):
        """
        Initialize smart refresh service
        
        Args:
            user: User to refresh feeds for
            batch_size: Number of feeds to process concurrently
            delay_between_feeds: Delay between feed batches (seconds)
            max_retries: Maximum retry attempts for failed feeds
            recalculate_priorities: Recalculate priorities before refresh
        """
        self.user = user
        self.batch_size = batch_size
        self.delay_between_feeds = delay_between_feeds
        self.max_retries = max_retries
        self.recalculate_priorities = recalculate_priorities
        
        # Progress tracking
        self.progress: Optional[RefreshProgress] = None
        self._refresh_history: Dict[str, RefreshProgress] = {}
        self._cancel_event = asyncio.Event()
        
        # Services
        self.priority_calculator = FeedPriorityCalculator(user)
        
        logger.debug(f"SmartRefreshService initialized for user {user.username} "
                    f"(batch_size: {batch_size}, delay: {delay_between_feeds}s)")
    
    async def refresh_feeds_by_priority(self, feed_ids: Optional[List[int]] = None) -> RefreshProgress:
        """
        Refresh feeds in priority order with smart batching
        
        Args:
            feed_ids: Specific feed IDs to refresh (None = all active feeds)
            
        Returns:
            RefreshProgress object with results
        """
        refresh_id = str(uuid.uuid4())[:8]
        
        try:
            # Get feeds to refresh
            if feed_ids:
                feeds = list(Feed.select().where(
                    Feed.id.in_(feed_ids) & (Feed.is_active == True)
                ))
            else:
                feeds = list(Feed.select().where(Feed.is_active == True))
            
            # Initialize progress tracking
            self.progress = RefreshProgress(
                refresh_id=refresh_id,
                user_id=self.user.id,
                total_feeds=len(feeds),
                batch_size=self.batch_size,
                priority_algorithm_version='v1.0'
            )
            
            if not feeds:
                logger.info(f"No active feeds to refresh for user {self.user.username}")
                self.progress.complete()
                self._refresh_history[refresh_id] = self.progress
                return self.progress
            
            self.progress.start()
            
            # Recalculate priorities if requested
            if self.recalculate_priorities:
                logger.info(f"Recalculating priorities for {len(feeds)} feeds")
                await self._recalculate_priorities(feeds)
            
            # Sort feeds by priority (highest first)
            prioritized_feeds = self._get_prioritized_feeds(feeds)
            
            # Process feeds in batches
            await self._process_feeds_in_batches(prioritized_feeds)
            
            # Record metrics
            await self._record_refresh_metrics()
            
            # Complete progress tracking
            if not self.progress.cancelled:
                self.progress.complete()
            
            # Store in history
            self._refresh_history[refresh_id] = self.progress
            
            return self.progress
            
        except Exception as e:
            logger.error(f"Smart refresh failed for user {self.user.username}: {e}")
            if self.progress:
                self.progress.add_error(0, f"Service error: {str(e)}")
                self.progress.complete()
                self._refresh_history[refresh_id] = self.progress
            raise
        finally:
            # Clear cancel event
            self._cancel_event.clear()
    
    async def _recalculate_priorities(self, feeds: List[Feed]):
        """Recalculate priorities for feeds before refresh"""
        try:
            priorities = self.priority_calculator.calculate_priorities_bulk(feeds, use_cache=False)
            
            # Update feed priorities in database
            for feed in feeds:
                if feed.id in priorities:
                    feed.priority_score = priorities[feed.id]
                    feed.save()
            
            logger.info(f"Recalculated priorities for {len(priorities)} feeds")
            
        except Exception as e:
            logger.warning(f"Failed to recalculate priorities: {e}")
    
    def _get_prioritized_feeds(self, feeds: List[Feed]) -> List[Feed]:
        """Get feeds sorted by priority score (highest first)"""
        # Sort by priority score descending
        prioritized = sorted(feeds, key=lambda f: f.priority_score or 0.0, reverse=True)
        
        if prioritized:
            logger.debug(f"Feed priority order: {prioritized[0].title} ({prioritized[0].priority_score:.3f}) "
                        f"to {prioritized[-1].title} ({prioritized[-1].priority_score:.3f})")
        
        return prioritized
    
    async def _process_feeds_in_batches(self, feeds: List[Feed]):
        """Process feeds in priority-ordered batches"""
        total_feeds = len(feeds)
        completed_feeds = 0
        successful_refreshes = 0
        failed_refreshes = 0
        
        # Process in batches
        for i in range(0, total_feeds, self.batch_size):
            # Check for cancellation
            if self._cancel_event.is_set():
                self.progress.cancel()
                return
            
            # Get batch
            batch = feeds[i:i + self.batch_size]
            batch_size = len(batch)
            
            logger.info(f"Processing batch {i//self.batch_size + 1}: "
                       f"{batch_size} feeds (priority: {batch[0].priority_score:.3f} to {batch[-1].priority_score:.3f})")
            
            # Process batch
            batch_results = await self._process_feed_batch(batch)
            
            # Update counters
            completed_feeds += batch_size
            for result in batch_results:
                if result.success:
                    successful_refreshes += 1
                    # Update posting history if articles were added
                    if hasattr(result, 'articles_added') and result.articles_added > 0:
                        self.priority_calculator.update_posting_history(
                            result.feed, result.articles_added
                        )
                else:
                    failed_refreshes += 1
                    self.progress.add_error(result.feed.id, result.error_message or "Unknown error")
                    # Update consecutive failure count
                    await self._update_failure_count(result.feed, increment=True)
            
            # Update progress
            self.progress.update_progress(completed_feeds, successful_refreshes, failed_refreshes)
            
            # Delay between batches (except for last batch)
            if i + self.batch_size < total_feeds and self.delay_between_feeds > 0:
                logger.debug(f"Waiting {self.delay_between_feeds}s before next batch")
                
                try:
                    await asyncio.wait_for(self._cancel_event.wait(), timeout=self.delay_between_feeds)
                    # If we get here, cancellation was requested
                    self.progress.cancel()
                    return
                except asyncio.TimeoutError:
                    # Normal case - delay completed
                    pass
    
    async def _process_feed_batch(self, feeds: List[Feed]):
        """Process a batch of feeds with error handling"""
        try:
            # Import here to avoid circular imports
            from app.services.feed_fetcher import feed_fetcher
            
            # Process feeds concurrently within the batch
            results = await feed_fetcher.update_multiple_feeds(
                feeds,
                force=True,
                max_concurrent=min(self.batch_size, len(feeds))
            )
            
            # Update success/failure tracking for each feed
            for result in results:
                if result.success:
                    # Reset consecutive failure count on success
                    await self._update_failure_count(result.feed, increment=False)
                else:
                    logger.warning(f"Feed refresh failed: {result.feed.title} - {result.error_message}")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Return mock results for error handling
            from dataclasses import dataclass
            
            @dataclass
            class MockResult:
                success: bool
                feed: Feed
                error_message: str
                
            return [MockResult(
                success=False,
                feed=feed,
                error_message=str(e)
            ) for feed in feeds]
    
    async def _update_failure_count(self, feed: Feed, increment: bool):
        """Update consecutive failure count for a feed"""
        try:
            if increment:
                feed.consecutive_failures = (feed.consecutive_failures or 0) + 1
                if feed.consecutive_failures == 1:
                    # First failure - record timestamp
                    feed.last_checked = pendulum.now('UTC').to_datetime_string()
            else:
                # Success - reset failure count
                feed.consecutive_failures = 0
                feed.last_successful_refresh = pendulum.now('UTC').to_datetime_string()
            
            feed.save()
            
        except Exception as e:
            logger.warning(f"Failed to update failure count for feed {feed.id}: {e}")
    
    async def _record_refresh_metrics(self):
        """Record refresh metrics to database"""
        if not self.progress:
            return
        
        try:
            RefreshMetrics.create(
                refresh_started_at=self.progress.started_at or datetime.now(),
                feeds_processed=self.progress.completed_feeds,
                total_duration_seconds=self.progress.duration_seconds,
                batch_size=self.batch_size,
                priority_algorithm_version=self.progress.priority_algorithm_version,
                created_at=pendulum.now('UTC').to_datetime_string()
            )
            
            logger.debug(f"Recorded refresh metrics: {self.progress.completed_feeds} feeds, "
                        f"{self.progress.duration_seconds:.1f}s")
            
        except Exception as e:
            logger.warning(f"Failed to record refresh metrics: {e}")
    
    def get_refresh_progress(self) -> Optional[RefreshProgress]:
        """Get current refresh progress"""
        return self.progress
    
    def get_refresh_status(self, refresh_id: str) -> Optional[RefreshProgress]:
        """Get status of a specific refresh by ID"""
        return self._refresh_history.get(refresh_id)
    
    def cancel_refresh(self):
        """Cancel the current refresh operation"""
        if self.progress and self.progress.is_active:
            logger.info(f"Cancelling refresh {self.progress.refresh_id}")
            self._cancel_event.set()
    
    def get_failed_feeds(self, days: int = 7) -> List[Feed]:
        """
        Get feeds that have been failing consistently
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of feeds with consecutive failures
        """
        try:
            cutoff_date = pendulum.now().subtract(days=days)
            
            failed_feeds = list(Feed.select().where(
                (Feed.consecutive_failures >= 3) &
                (Feed.last_checked >= cutoff_date.to_datetime_string())
            ))
            
            logger.debug(f"Found {len(failed_feeds)} consistently failing feeds")
            return failed_feeds
            
        except Exception as e:
            logger.error(f"Error getting failed feeds: {e}")
            return []
    
    def get_refresh_history(self, limit: int = 10) -> List[RefreshProgress]:
        """Get recent refresh history"""
        # Sort by start time (most recent first)
        history = sorted(
            self._refresh_history.values(),
            key=lambda p: p.started_at or datetime.min,
            reverse=True
        )
        
        return history[:limit]
    
    async def refresh_single_feed(self, feed: Feed, max_retries: Optional[int] = None) -> bool:
        """
        Refresh a single feed with retry logic
        
        Args:
            feed: Feed to refresh
            max_retries: Override default max retries
            
        Returns:
            True if successful, False if failed
        """
        retries = max_retries if max_retries is not None else self.max_retries
        
        for attempt in range(retries + 1):
            try:
                from app.services.feed_fetcher import feed_fetcher
                
                results = await feed_fetcher.update_multiple_feeds([feed], force=True)
                
                if results and results[0].success:
                    logger.info(f"Successfully refreshed feed: {feed.title}")
                    await self._update_failure_count(feed, increment=False)
                    
                    # Update posting history if articles were added
                    if hasattr(results[0], 'articles_added') and results[0].articles_added > 0:
                        self.priority_calculator.update_posting_history(
                            feed, results[0].articles_added
                        )
                    
                    return True
                else:
                    error_msg = results[0].error_message if results else "No result returned"
                    logger.warning(f"Feed refresh failed (attempt {attempt + 1}): {feed.title} - {error_msg}")
                    
                    if attempt < retries:
                        # Exponential backoff
                        delay = 2 ** attempt
                        logger.debug(f"Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Feed refresh error (attempt {attempt + 1}): {feed.title} - {e}")
                
                if attempt < retries:
                    delay = 2 ** attempt
                    await asyncio.sleep(delay)
        
        # All attempts failed
        await self._update_failure_count(feed, increment=True)
        logger.error(f"Feed refresh failed after {retries + 1} attempts: {feed.title}")
        return False
    
    def get_priority_stats(self) -> Dict:
        """Get statistics about feed priorities"""
        try:
            feeds = list(Feed.select().where(Feed.is_active == True))
            
            if not feeds:
                return {'total_feeds': 0}
            
            priorities = [f.priority_score or 0.0 for f in feeds]
            
            stats = {
                'total_feeds': len(feeds),
                'avg_priority': sum(priorities) / len(priorities),
                'max_priority': max(priorities),
                'min_priority': min(priorities),
                'high_priority_feeds': len([p for p in priorities if p >= 0.7]),
                'medium_priority_feeds': len([p for p in priorities if 0.3 <= p < 0.7]),
                'low_priority_feeds': len([p for p in priorities if p < 0.3])
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting priority stats: {e}")
            return {'error': str(e)}
    
    def __repr__(self):
        return (f"SmartRefreshService(user={self.user.username}, batch_size={self.batch_size}, "
                f"delay={self.delay_between_feeds}s, max_retries={self.max_retries})")