"""
FeedPriorityCalculator - Multi-factor scoring algorithm for smart feed refresh

Calculates priority scores for feeds based on:
- Unread article count (40% weight)
- User engagement/activity (30% weight)  
- Posting frequency (20% weight)
- Read percentage (10% weight)
"""

import logging
import pendulum
from datetime import timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from app.models.base import Feed, FeedPostingHistory
from app.models.article import User, Article, ReadStatus
from app.core.database import db

logger = logging.getLogger(__name__)


class FeedPriorityCalculator:
    """Calculate priority scores for feeds using multiple factors"""
    
    def __init__(self, user: User):
        """Initialize calculator for a specific user"""
        self.user = user
        
        # Configurable weights for different factors
        self.weights = {
            'unread_count': 0.4,        # 40% - Most important factor
            'user_activity': 0.3,       # 30% - User engagement with feed
            'posting_frequency': 0.2,   # 20% - How often feed posts
            'read_percentage': 0.1      # 10% - Historical read rate
        }
        
        # Caching for efficiency
        self._article_counts_cache = {}
        self._posting_history_cache = {}
        
    def calculate_priority(self, feed: Feed, use_cache: bool = False) -> float:
        """
        Calculate overall priority score for a feed
        
        Args:
            feed: Feed to calculate priority for
            use_cache: If True, return cached score if available
            
        Returns:
            Priority score between 0.0 and 1.0 (higher = more priority)
        """
        try:
            # Return cached score if requested and available
            if use_cache and feed.priority_score > 0:
                logger.debug(f"Using cached priority score for {feed.title}: {feed.priority_score}")
                return feed.priority_score
            
            # Inactive feeds get zero priority
            if not feed.is_active:
                logger.debug(f"Feed {feed.title} is inactive, priority = 0.0")
                return 0.0
            
            # Calculate individual factor scores
            unread_score = self._calculate_unread_score(feed)
            activity_score = self._calculate_user_engagement_score(feed)
            frequency_score = self._calculate_posting_frequency_score(feed)
            read_percentage_score = self._calculate_read_percentage_score(feed)
            
            # Weighted combination
            priority_score = (
                unread_score * self.weights['unread_count'] +
                activity_score * self.weights['user_activity'] +
                frequency_score * self.weights['posting_frequency'] +
                read_percentage_score * self.weights['read_percentage']
            )
            
            # Ensure score is in valid range
            priority_score = max(0.0, min(1.0, priority_score))
            
            # Cache the score in the database
            feed.priority_score = priority_score
            feed.save()
            
            logger.debug(f"Calculated priority for {feed.title}: {priority_score:.3f} "
                        f"(unread: {unread_score:.2f}, activity: {activity_score:.2f}, "
                        f"frequency: {frequency_score:.2f}, read%: {read_percentage_score:.2f})")
            
            return priority_score
            
        except Exception as e:
            logger.error(f"Error calculating priority for feed {feed.title}: {e}")
            return 0.0
    
    def _calculate_unread_score(self, feed: Feed) -> float:
        """Calculate score based on unread article count (0.0 to 1.0)"""
        try:
            # Get unread count for this user
            unread_count = self._get_unread_count(feed)
            
            # Normalize using logarithmic scale (diminishing returns for very high counts)
            # Score = log(unread + 1) / log(max_reasonable_unread + 1)
            max_reasonable_unread = 50  # Articles beyond this don't increase priority much
            
            if unread_count == 0:
                return 0.0
            
            import math
            score = math.log(unread_count + 1) / math.log(max_reasonable_unread + 1)
            return min(1.0, score)
            
        except Exception as e:
            logger.warning(f"Error calculating unread score for {feed.title}: {e}")
            return 0.0
    
    def _calculate_user_engagement_score(self, feed: Feed) -> float:
        """Calculate score based on user engagement with feed (0.0 to 1.0)"""
        try:
            # Get recent articles from this feed (last 30 days)
            cutoff_date = pendulum.now().subtract(days=30)
            
            recent_articles = Article.select().where(
                (Article.feed == feed) &
                (Article.created_at >= cutoff_date.to_datetime_string())
            )
            
            if not recent_articles.exists():
                return 0.0
            
            # Calculate engagement metrics
            total_articles = recent_articles.count()
            read_count = 0
            starred_count = 0
            
            for article in recent_articles:
                try:
                    read_status = ReadStatus.get(
                        (ReadStatus.user == self.user) & 
                        (ReadStatus.article == article)
                    )
                    if read_status.is_read:
                        read_count += 1
                    if read_status.is_starred:
                        starred_count += 1
                except ReadStatus.DoesNotExist:
                    pass
            
            # Calculate engagement score
            read_rate = read_count / total_articles if total_articles > 0 else 0
            star_rate = starred_count / total_articles if total_articles > 0 else 0
            
            # Weighted combination: read rate (70%) + star rate (30%)
            engagement_score = (read_rate * 0.7) + (star_rate * 0.3)
            
            return min(1.0, engagement_score)
            
        except Exception as e:
            logger.warning(f"Error calculating engagement score for {feed.title}: {e}")
            return 0.0
    
    def _calculate_posting_frequency_score(self, feed: Feed) -> float:
        """Calculate score based on posting frequency (0.0 to 1.0)"""
        try:
            # Try to use cached frequency from feed model first
            if feed.posting_frequency_days and feed.posting_frequency_days > 0:
                # Convert frequency to score (more frequent = higher score)
                # Daily posts (1.0 days) = 1.0 score, weekly (7.0 days) = ~0.3 score
                frequency_score = max(0.0, min(1.0, 2.0 / feed.posting_frequency_days))
                return frequency_score
            
            # Calculate from posting history if not cached
            posting_history = self._get_posting_history(feed, days=14)
            
            if not posting_history:
                return 0.1  # Default low score for feeds with no history
            
            # Calculate average posting frequency
            total_articles = sum(entry.articles_count for entry in posting_history)
            days_span = len(posting_history)
            
            if days_span == 0:
                return 0.1
            
            articles_per_day = total_articles / days_span
            
            # Convert to score (normalize around 1-2 articles per day as optimal)
            if articles_per_day >= 1.0:
                frequency_score = min(1.0, articles_per_day / 3.0)  # Cap at 3 articles/day for max score
            else:
                frequency_score = articles_per_day  # Linear below 1 article/day
            
            # Cache the calculated frequency
            if days_span >= 7:  # Only cache if we have at least a week of data
                feed.posting_frequency_days = days_span / len([h for h in posting_history if h.articles_count > 0])
                feed.save()
            
            return frequency_score
            
        except Exception as e:
            logger.warning(f"Error calculating frequency score for {feed.title}: {e}")
            return 0.1
    
    def _calculate_read_percentage_score(self, feed: Feed) -> float:
        """Calculate score based on historical read percentage (0.0 to 1.0)"""
        try:
            # Get recent articles (last 60 days for broader sample)
            cutoff_date = pendulum.now().subtract(days=60)
            
            articles = Article.select().where(
                (Article.feed == feed) &
                (Article.created_at >= cutoff_date.to_datetime_string())
            )
            
            total_count = articles.count()
            if total_count == 0:
                return 0.0
            
            # Count read articles
            read_count = 0
            for article in articles:
                try:
                    read_status = ReadStatus.get(
                        (ReadStatus.user == self.user) & 
                        (ReadStatus.article == article)
                    )
                    if read_status.is_read:
                        read_count += 1
                except ReadStatus.DoesNotExist:
                    pass
            
            read_percentage = read_count / total_count
            
            # Use inverse relationship: lower read percentage = higher priority
            # (feeds with many unread articles should be prioritized)
            score = 1.0 - read_percentage
            
            return score
            
        except Exception as e:
            logger.warning(f"Error calculating read percentage score for {feed.title}: {e}")
            return 0.5
    
    def _get_unread_count(self, feed: Feed) -> int:
        """Get count of unread articles for this feed and user"""
        cache_key = f"unread_{feed.id}"
        if cache_key in self._article_counts_cache:
            return self._article_counts_cache[cache_key]
        
        try:
            # Get all articles for this feed
            articles = Article.select().where(Article.feed == feed)
            
            unread_count = 0
            for article in articles:
                try:
                    read_status = ReadStatus.get(
                        (ReadStatus.user == self.user) & 
                        (ReadStatus.article == article)
                    )
                    if not read_status.is_read:
                        unread_count += 1
                except ReadStatus.DoesNotExist:
                    # No read status = unread
                    unread_count += 1
            
            self._article_counts_cache[cache_key] = unread_count
            return unread_count
            
        except Exception as e:
            logger.error(f"Error getting unread count for {feed.title}: {e}")
            return 0
    
    def _get_posting_history(self, feed: Feed, days: int = 14) -> List[FeedPostingHistory]:
        """Get posting history for a feed over specified days"""
        cache_key = f"history_{feed.id}_{days}"
        if cache_key in self._posting_history_cache:
            return self._posting_history_cache[cache_key]
        
        try:
            cutoff_date = pendulum.now().subtract(days=days).date()
            
            history = list(FeedPostingHistory.select().where(
                (FeedPostingHistory.feed == feed) &
                (FeedPostingHistory.posting_date >= cutoff_date)
            ).order_by(FeedPostingHistory.posting_date.desc()))
            
            self._posting_history_cache[cache_key] = history
            return history
            
        except Exception as e:
            logger.error(f"Error getting posting history for {feed.title}: {e}")
            return []
    
    def calculate_priorities_bulk(self, feeds: List[Feed], use_cache: bool = False) -> Dict[int, float]:
        """
        Calculate priorities for multiple feeds efficiently
        
        Args:
            feeds: List of feeds to calculate priorities for
            use_cache: If True, use cached scores where available
            
        Returns:
            Dictionary mapping feed_id to priority_score
        """
        priorities = {}
        
        logger.info(f"Calculating priorities for {len(feeds)} feeds (use_cache={use_cache})")
        
        for feed in feeds:
            try:
                priority = self.calculate_priority(feed, use_cache=use_cache)
                priorities[feed.id] = priority
            except Exception as e:
                logger.error(f"Error calculating priority for feed {feed.id}: {e}")
                priorities[feed.id] = 0.0
        
        logger.info(f"Completed priority calculations. Average score: "
                   f"{sum(priorities.values()) / len(priorities):.3f}")
        
        return priorities
    
    def update_posting_history(self, feed: Feed, articles_added: int, posting_date: Optional[str] = None):
        """
        Update posting history for a feed after refresh
        
        Args:
            feed: Feed that was refreshed
            articles_added: Number of new articles added
            posting_date: Date of posting (defaults to today)
        """
        try:
            if articles_added <= 0:
                return
            
            post_date = pendulum.parse(posting_date).date() if posting_date else pendulum.now().date()
            
            # Check if entry already exists for this date
            try:
                existing = FeedPostingHistory.get(
                    (FeedPostingHistory.feed == feed) &
                    (FeedPostingHistory.posting_date == post_date)
                )
                existing.articles_count += articles_added
                existing.save()
                logger.debug(f"Updated posting history for {feed.title}: +{articles_added} articles on {post_date}")
            except FeedPostingHistory.DoesNotExist:
                # Create new entry
                FeedPostingHistory.create(
                    feed=feed,
                    posting_date=post_date,
                    articles_count=articles_added,
                    created_at=pendulum.now().to_datetime_string()
                )
                logger.debug(f"Created posting history entry for {feed.title}: {articles_added} articles on {post_date}")
            
            # Update feed's article count
            feed.total_articles_fetched = (feed.total_articles_fetched or 0) + articles_added
            feed.last_post_date = pendulum.now().to_datetime_string()
            feed.save()
            
            # Clear caches for this feed
            self._clear_feed_caches(feed)
            
        except Exception as e:
            logger.error(f"Error updating posting history for {feed.title}: {e}")
    
    def update_user_engagement(self, feed: Feed):
        """Update user engagement score for a feed based on recent activity"""
        try:
            engagement_score = self._calculate_user_engagement_score(feed)
            feed.user_engagement_score = engagement_score
            feed.save()
            
            logger.debug(f"Updated engagement score for {feed.title}: {engagement_score:.3f}")
            
        except Exception as e:
            logger.error(f"Error updating engagement score for {feed.title}: {e}")
    
    def _clear_feed_caches(self, feed: Feed):
        """Clear cached data for a specific feed"""
        keys_to_remove = [key for key in self._article_counts_cache.keys() if str(feed.id) in key]
        for key in keys_to_remove:
            del self._article_counts_cache[key]
        
        keys_to_remove = [key for key in self._posting_history_cache.keys() if str(feed.id) in key]
        for key in keys_to_remove:
            del self._posting_history_cache[key]
    
    def get_prioritized_feeds(self, active_only: bool = True, limit: Optional[int] = None) -> List[Feed]:
        """
        Get feeds ordered by priority score (highest first)
        
        Args:
            active_only: If True, only return active feeds
            limit: Maximum number of feeds to return
            
        Returns:
            List of feeds ordered by priority (highest first)
        """
        try:
            query = Feed.select()
            
            if active_only:
                query = query.where(Feed.is_active == True)
            
            # Order by priority score (highest first)
            query = query.order_by(Feed.priority_score.desc())
            
            if limit:
                query = query.limit(limit)
            
            feeds = list(query)
            
            logger.info(f"Retrieved {len(feeds)} feeds ordered by priority")
            if feeds:
                logger.debug(f"Top feed: {feeds[0].title} (score: {feeds[0].priority_score:.3f})")
                if len(feeds) > 1:
                    logger.debug(f"Bottom feed: {feeds[-1].title} (score: {feeds[-1].priority_score:.3f})")
            
            return feeds
            
        except Exception as e:
            logger.error(f"Error getting prioritized feeds: {e}")
            return []