import pytest
import sqlite3
from datetime import datetime, timedelta
from peewee import DoesNotExist
from app.core.database import db
from app.models.base import Feed, Category


def test_feed_has_accessibility_fields():
    """Test that Feed model has the new accessibility tracking fields"""
    # Create a test feed
    category = Category.create(name="Test Category")
    feed = Feed.create(
        url="https://example.com/feed.xml",
        title="Test Feed", 
        category=category
    )
    
    # Check that the new fields exist and have default values
    assert hasattr(feed, 'last_checked')
    assert hasattr(feed, 'accessible')
    assert hasattr(feed, 'consecutive_failures')
    
    # Check default values
    assert feed.last_checked is None
    assert feed.accessible is True  # Should default to True
    assert feed.consecutive_failures == 0


def test_feed_accessibility_fields_can_be_updated():
    """Test that accessibility fields can be updated"""
    category = Category.create(name="Test Category 2")
    feed = Feed.create(
        url="https://example.com/feed2.xml",
        title="Test Feed 2",
        category=category
    )
    
    # Update accessibility fields
    now = datetime.now()
    feed.last_checked = now
    feed.accessible = False
    feed.consecutive_failures = 3
    feed.save()
    
    # Reload from database and verify
    reloaded = Feed.get_by_id(feed.id)
    assert reloaded.last_checked == now
    assert reloaded.accessible is False
    assert reloaded.consecutive_failures == 3


def test_feed_check_log_model_exists():
    """Test that FeedCheckLog model exists and has correct fields"""
    from app.models.base import FeedCheckLog
    
    # Test model structure
    assert hasattr(FeedCheckLog, 'id')
    assert hasattr(FeedCheckLog, 'feed')
    assert hasattr(FeedCheckLog, 'checked_at')
    assert hasattr(FeedCheckLog, 'status_code')
    assert hasattr(FeedCheckLog, 'error_message')
    assert hasattr(FeedCheckLog, 'response_time_ms')
    assert hasattr(FeedCheckLog, 'is_success')
    assert hasattr(FeedCheckLog, 'user_agent')
    assert hasattr(FeedCheckLog, 'created_at')


def test_feed_check_log_creation():
    """Test creating FeedCheckLog entries"""
    from app.models.base import FeedCheckLog
    
    category = Category.create(name="Log Test Category")
    feed = Feed.create(
        url="https://example.com/logtest.xml",
        title="Log Test Feed",
        category=category
    )
    
    # Create successful check log
    success_log = FeedCheckLog.create(
        feed=feed,
        status_code=200,
        response_time_ms=850,
        is_success=True
    )
    
    assert success_log.feed.id == feed.id
    assert success_log.status_code == 200
    assert success_log.response_time_ms == 850
    assert success_log.is_success is True
    assert success_log.error_message is None
    
    # Create failed check log
    failed_log = FeedCheckLog.create(
        feed=feed,
        error_message="Connection timeout",
        response_time_ms=10000,
        is_success=False
    )
    
    assert failed_log.feed.id == feed.id
    assert failed_log.status_code is None
    assert failed_log.error_message == "Connection timeout"
    assert failed_log.is_success is False


def test_feed_check_log_foreign_key_cascade():
    """Test that deleting a feed deletes associated check logs"""
    from app.models.base import FeedCheckLog
    
    category = Category.create(name="Cascade Test Category")
    feed = Feed.create(
        url="https://example.com/cascade.xml",
        title="Cascade Test Feed",
        category=category
    )
    
    # Create check logs for the feed
    log1 = FeedCheckLog.create(feed=feed, is_success=True, status_code=200)
    log2 = FeedCheckLog.create(feed=feed, is_success=False, error_message="Error")
    
    # Verify logs exist
    assert FeedCheckLog.select().where(FeedCheckLog.feed == feed).count() == 2
    
    # Delete the feed
    feed.delete_instance()
    
    # Verify logs are also deleted (cascade)
    assert FeedCheckLog.select().where(FeedCheckLog.id.in_([log1.id, log2.id])).count() == 0


def test_find_broken_feeds_query():
    """Test query to find feeds broken for 7+ days"""
    from app.models.base import FeedCheckLog
    
    category = Category.create(name="Broken Feeds Category")
    
    # Create feeds with different states
    working_feed = Feed.create(
        url="https://working.com/feed.xml",
        title="Working Feed",
        category=category,
        last_checked=datetime.now(),
        accessible=True,
        consecutive_failures=0
    )
    
    recently_broken_feed = Feed.create(
        url="https://recent.com/feed.xml", 
        title="Recently Broken Feed",
        category=category,
        last_checked=datetime.now() - timedelta(days=3),
        accessible=False,
        consecutive_failures=5
    )
    
    old_broken_feed = Feed.create(
        url="https://broken.com/feed.xml",
        title="Long Broken Feed", 
        category=category,
        last_checked=datetime.now() - timedelta(days=10),
        accessible=False,
        consecutive_failures=15
    )
    
    never_checked_feed = Feed.create(
        url="https://never.com/feed.xml",
        title="Never Checked Feed",
        category=category,
        accessible=False  # Should be included as potentially broken
    )
    
    # Query for feeds broken for 7+ days
    seven_days_ago = datetime.now() - timedelta(days=7)
    broken_feeds = Feed.select().where(
        (Feed.category == category) &
        (Feed.accessible == False) &
        ((Feed.last_checked.is_null()) | (Feed.last_checked <= seven_days_ago))
    )
    
    broken_feed_ids = [f.id for f in broken_feeds]
    
    # Should include old_broken_feed and never_checked_feed
    assert old_broken_feed.id in broken_feed_ids
    assert never_checked_feed.id in broken_feed_ids
    
    # Should NOT include working_feed or recently_broken_feed
    assert working_feed.id not in broken_feed_ids
    assert recently_broken_feed.id not in broken_feed_ids


def test_feed_check_history_query():
    """Test query to get recent check history for a feed"""
    from app.models.base import FeedCheckLog
    
    category = Category.create(name="History Test Category")
    feed = Feed.create(
        url="https://history.com/feed.xml",
        title="History Test Feed",
        category=category
    )
    
    # Create multiple check log entries
    logs = []
    base_time = datetime.now() - timedelta(hours=24)
    
    for i in range(15):
        log = FeedCheckLog.create(
            feed=feed,
            checked_at=base_time + timedelta(hours=i),
            is_success=(i % 3 != 0),  # Every 3rd check fails
            status_code=200 if (i % 3 != 0) else None,
            error_message=None if (i % 3 != 0) else f"Error {i}",
            response_time_ms=800 + (i * 10)
        )
        logs.append(log)
    
    # Query recent history (limit 10)
    recent_history = (FeedCheckLog
                     .select()
                     .where(FeedCheckLog.feed == feed)
                     .order_by(FeedCheckLog.checked_at.desc())
                     .limit(10))
    
    history_list = list(recent_history)
    
    # Should return 10 most recent entries
    assert len(history_list) == 10
    
    # Should be ordered by most recent first
    assert history_list[0].checked_at > history_list[-1].checked_at
    
    # Calculate success rate
    total_checks = FeedCheckLog.select().where(FeedCheckLog.feed == feed).count()
    successful_checks = FeedCheckLog.select().where(
        (FeedCheckLog.feed == feed) & (FeedCheckLog.is_success == True)
    ).count()
    
    assert total_checks == 15
    success_rate = successful_checks / total_checks
    assert 0.6 <= success_rate <= 0.7  # About 10/15 should be successful


def test_feed_health_summary_query():
    """Test query to get feed health summary for category"""  
    category = Category.create(name="Summary Test Category")
    
    # Create feeds with various states
    Feed.create(url="https://good1.com/feed.xml", category=category, accessible=True)
    Feed.create(url="https://good2.com/feed.xml", category=category, accessible=True)
    Feed.create(url="https://bad1.com/feed.xml", category=category, accessible=False)
    Feed.create(url="https://never.com/feed.xml", category=category)  # Never checked
    
    # Query health summary
    from peewee import fn, Case
    
    summary = (Feed
              .select(
                  fn.COUNT(Feed.id).alias('total_feeds'),
                  fn.SUM(Case(None, [(Feed.accessible == True, 1)], 0)).alias('accessible_feeds'),
                  fn.SUM(Case(None, [(Feed.accessible == False, 1)], 0)).alias('broken_feeds'),
                  fn.SUM(Case(None, [(Feed.last_checked.is_null(), 1)], 0)).alias('never_checked')
              )
              .where(Feed.category == category)
              .scalar(as_tuple=True))
    
    total_feeds, accessible_feeds, broken_feeds, never_checked = summary
    
    assert total_feeds == 4
    assert accessible_feeds == 2  # good1, good2 
    assert broken_feeds == 1      # bad1
    assert never_checked == 1     # never (null last_checked)