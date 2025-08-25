"""
Tests for smart refresh system database migration and models
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
import pendulum

from app.core.database import db, init_database
from app.models.base import Feed, Category, FeedPostingHistory, RefreshMetrics
import sys
import importlib.util

# Import migration module by file path since it starts with a number
spec = importlib.util.spec_from_file_location(
    "smart_refresh_migration", 
    "migrations/014_smart_refresh_system.py"
)
smart_refresh_migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smart_refresh_migration)

up = smart_refresh_migration.up
down = smart_refresh_migration.down


class TestSmartRefreshMigration:
    """Test the smart refresh system migration"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        # Create temporary database file
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)
        
        # Initialize database with temp path
        original_path = db.database
        db.init(db_path)
        
        # Initialize schema
        init_database()
        
        yield db_path
        
        # Cleanup
        db.close()
        os.unlink(db_path)
        db.init(original_path)
    
    def test_migration_up(self, temp_db):
        """Test that migration applies correctly"""
        # Apply migration
        up()
        
        # Test that new fields exist in feeds table
        cursor = db.execute_sql("PRAGMA table_info(feeds)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # Check new fields were added
        expected_fields = {
            'priority_score': 'REAL',
            'last_post_date': 'DATETIME',
            'posting_frequency_days': 'REAL',
            'total_articles_fetched': 'INTEGER',
            'user_engagement_score': 'REAL'
        }
        
        for field_name, field_type in expected_fields.items():
            assert field_name in columns, f"Field {field_name} not found in feeds table"
            assert field_type in columns[field_name].upper(), f"Field {field_name} has wrong type: {columns[field_name]}"
        
        # Test that new tables exist
        cursor = db.execute_sql("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'feed_posting_history' in tables, "feed_posting_history table not created"
        assert 'refresh_metrics' in tables, "refresh_metrics table not created"
        
        # Test that indexes were created
        cursor = db.execute_sql("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_feeds_priority_score',
            'idx_feeds_last_post_date',
            'idx_feed_posting_history_feed_date',
            'idx_feed_posting_history_date',
            'idx_refresh_metrics_started_at'
        ]
        
        for index_name in expected_indexes:
            assert index_name in indexes, f"Index {index_name} not created"
    
    def test_migration_down(self, temp_db):
        """Test that migration rolls back correctly"""
        # Apply migration first
        up()
        
        # Verify fields exist
        cursor = db.execute_sql("PRAGMA table_info(feeds)")
        columns = [row[1] for row in cursor.fetchall()]
        assert 'priority_score' in columns
        
        # Roll back migration
        down()
        
        # Test that new fields were removed
        cursor = db.execute_sql("PRAGMA table_info(feeds)")
        columns = [row[1] for row in cursor.fetchall()]
        
        removed_fields = ['priority_score', 'last_post_date', 'posting_frequency_days', 
                         'total_articles_fetched', 'user_engagement_score']
        
        for field_name in removed_fields:
            assert field_name not in columns, f"Field {field_name} was not removed"
        
        # Test that new tables were dropped
        cursor = db.execute_sql("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'feed_posting_history' not in tables, "feed_posting_history table not dropped"
        assert 'refresh_metrics' not in tables, "refresh_metrics table not dropped"
    
    def test_migration_idempotent(self, temp_db):
        """Test that migration can be run multiple times safely"""
        # Apply migration twice
        up()
        up()  # Should not fail
        
        # Verify everything still works
        cursor = db.execute_sql("PRAGMA table_info(feeds)")
        columns = [row[1] for row in cursor.fetchall()]
        assert 'priority_score' in columns


class TestSmartRefreshModels:
    """Test the new smart refresh models"""
    
    @pytest.fixture
    def temp_db_with_models(self):
        """Create a temporary database with models"""
        # Create temporary database file
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)
        
        # Initialize database
        original_path = db.database
        db.init(db_path)
        
        # Initialize schema and apply migration
        init_database()
        up()
        
        yield db_path
        
        # Cleanup
        db.close()
        os.unlink(db_path)
        db.init(original_path)
    
    def test_feed_priority_fields(self, temp_db_with_models):
        """Test Feed model with new priority fields"""
        # Create category first
        category = Category.create(name="Test Category")
        
        # Create feed with priority fields
        feed = Feed.create(
            url="https://example.com/feed.xml",
            title="Test Feed",
            category=category,
            priority_score=0.75,
            last_post_date=datetime.now(),
            posting_frequency_days=2.5,
            total_articles_fetched=100,
            user_engagement_score=0.85
        )
        
        # Verify fields were saved correctly
        saved_feed = Feed.get_by_id(feed.id)
        assert saved_feed.priority_score == 0.75
        assert saved_feed.posting_frequency_days == 2.5
        assert saved_feed.total_articles_fetched == 100
        assert saved_feed.user_engagement_score == 0.85
        assert saved_feed.last_post_date is not None
    
    def test_feed_posting_history_model(self, temp_db_with_models):
        """Test FeedPostingHistory model"""
        # Create category and feed
        category = Category.create(name="Test Category")
        feed = Feed.create(
            url="https://example.com/feed.xml",
            title="Test Feed",
            category=category
        )
        
        # Create posting history entry
        posting_date = datetime.now().date()
        history = FeedPostingHistory.create(
            feed=feed,
            posting_date=posting_date,
            articles_count=3
        )
        
        # Verify entry was saved correctly
        saved_history = FeedPostingHistory.get_by_id(history.id)
        assert saved_history.feed.id == feed.id
        assert saved_history.articles_count == 3
        assert saved_history.posting_date.date() == posting_date
        assert saved_history.created_at is not None
    
    def test_refresh_metrics_model(self, temp_db_with_models):
        """Test RefreshMetrics model"""
        refresh_started = datetime.now()
        
        # Create refresh metrics entry
        metrics = RefreshMetrics.create(
            refresh_started_at=refresh_started,
            feeds_processed=25,
            total_duration_seconds=45.5,
            batch_size=10,
            priority_algorithm_version="v1.0"
        )
        
        # Verify entry was saved correctly
        saved_metrics = RefreshMetrics.get_by_id(metrics.id)
        assert saved_metrics.feeds_processed == 25
        assert saved_metrics.total_duration_seconds == 45.5
        assert saved_metrics.batch_size == 10
        assert saved_metrics.priority_algorithm_version == "v1.0"
        assert saved_metrics.refresh_started_at.replace(microsecond=0) == refresh_started.replace(microsecond=0)
        assert saved_metrics.created_at is not None
    
    def test_feed_posting_history_relationships(self, temp_db_with_models):
        """Test relationships between Feed and FeedPostingHistory"""
        # Create feed
        category = Category.create(name="Test Category")
        feed = Feed.create(
            url="https://example.com/feed.xml",
            title="Test Feed",
            category=category
        )
        
        # Create multiple posting history entries
        base_date = datetime.now().date()
        for i in range(3):
            FeedPostingHistory.create(
                feed=feed,
                posting_date=base_date - timedelta(days=i),
                articles_count=i + 1
            )
        
        # Test backref relationship
        history_entries = list(feed.posting_history)
        assert len(history_entries) == 3
        
        # Test that we can query by feed
        feed_history = FeedPostingHistory.select().where(FeedPostingHistory.feed == feed)
        assert feed_history.count() == 3
    
    def test_feed_default_values(self, temp_db_with_models):
        """Test that Feed model has correct default values for new fields"""
        category = Category.create(name="Test Category")
        
        # Create feed without specifying priority fields
        feed = Feed.create(
            url="https://example.com/feed.xml",
            title="Test Feed",
            category=category
        )
        
        # Verify default values
        assert feed.priority_score == 0.0
        assert feed.posting_frequency_days == 1.0
        assert feed.total_articles_fetched == 0
        assert feed.user_engagement_score == 0.0
        assert feed.last_post_date is None
    
    def test_feed_priority_score_indexing(self, temp_db_with_models):
        """Test that priority score index works for ordering"""
        category = Category.create(name="Test Category")
        
        # Create feeds with different priorities
        feed1 = Feed.create(url="https://example1.com/feed.xml", title="Low Priority", 
                           category=category, priority_score=0.2)
        feed2 = Feed.create(url="https://example2.com/feed.xml", title="High Priority", 
                           category=category, priority_score=0.8)
        feed3 = Feed.create(url="https://example3.com/feed.xml", title="Medium Priority", 
                           category=category, priority_score=0.5)
        
        # Query feeds ordered by priority (highest first)
        ordered_feeds = list(Feed.select().order_by(Feed.priority_score.desc()))
        
        # Verify correct order
        assert ordered_feeds[0].id == feed2.id  # High priority first
        assert ordered_feeds[1].id == feed3.id  # Medium priority second
        assert ordered_feeds[2].id == feed1.id  # Low priority last
    
    def test_posting_history_date_queries(self, temp_db_with_models):
        """Test date-based queries on posting history"""
        category = Category.create(name="Test Category")
        feed = Feed.create(url="https://example.com/feed.xml", title="Test Feed", category=category)
        
        # Create history entries for different dates
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        FeedPostingHistory.create(feed=feed, posting_date=today, articles_count=5)
        FeedPostingHistory.create(feed=feed, posting_date=yesterday, articles_count=3)
        FeedPostingHistory.create(feed=feed, posting_date=week_ago, articles_count=2)
        
        # Test date range queries
        recent_history = FeedPostingHistory.select().where(
            FeedPostingHistory.posting_date >= yesterday
        )
        assert recent_history.count() == 2
        
        # Test specific date query
        today_history = FeedPostingHistory.select().where(
            FeedPostingHistory.posting_date == today
        )
        assert today_history.count() == 1
        assert today_history[0].articles_count == 5