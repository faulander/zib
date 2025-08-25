"""
Tests for FeedPriorityCalculator - the multi-factor scoring algorithm
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
import pendulum

from app.core.database import db, init_database
from app.models.base import Feed, Category, FeedPostingHistory
from app.models.article import User, Article, ReadStatus
from app.services.priority_calculator import FeedPriorityCalculator


class TestFeedPriorityCalculator:
    """Test the priority calculation algorithm"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        # Create temporary database file
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)
        
        # Initialize database with temp path
        original_path = db.database
        db.init(db_path)
        
        # Initialize schema and models
        init_database()
        
        yield db_path
        
        # Cleanup
        db.close()
        os.unlink(db_path)
        db.init(original_path)
    
    @pytest.fixture
    def sample_data(self, temp_db):
        """Create sample data for testing"""
        # Create user
        user = User.create(
            username="testuser",
            auto_refresh_feeds=True,
            auto_refresh_interval_minutes=10
        )
        
        # Create category
        category = Category.create(name="Test Category")
        
        # Create feeds with different characteristics
        high_priority_feed = Feed.create(
            url="https://high-priority.com/feed.xml",
            title="High Priority Feed",
            category=category,
            is_active=True
        )
        
        medium_priority_feed = Feed.create(
            url="https://medium-priority.com/feed.xml", 
            title="Medium Priority Feed",
            category=category,
            is_active=True
        )
        
        low_priority_feed = Feed.create(
            url="https://low-priority.com/feed.xml",
            title="Low Priority Feed", 
            category=category,
            is_active=True
        )
        
        return {
            'user': user,
            'category': category,
            'feeds': {
                'high': high_priority_feed,
                'medium': medium_priority_feed,
                'low': low_priority_feed
            }
        }
    
    def test_calculator_initialization(self, temp_db):
        """Test FeedPriorityCalculator can be initialized"""
        user = User.create(username="testuser")
        calculator = FeedPriorityCalculator(user)
        
        assert calculator.user.id == user.id
        assert calculator.weights['unread_count'] == 0.4
        assert calculator.weights['user_activity'] == 0.3
        assert calculator.weights['posting_frequency'] == 0.2
        assert calculator.weights['read_percentage'] == 0.1
    
    def test_unread_count_scoring(self, sample_data):
        """Test unread count factor calculation"""
        user = sample_data['user']
        feed = sample_data['feeds']['high']
        calculator = FeedPriorityCalculator(user)
        
        # Create articles - some read, some unread
        now = pendulum.now()
        for i in range(10):
            article = Article.create(
                feed=feed,
                title=f"Article {i}",
                url=f"https://example.com/article-{i}",
                guid=f"article-{i}",
                published_date=now.subtract(days=i).to_datetime_string()
            )
            
            # Mark first 3 articles as read
            if i < 3:
                ReadStatus.create(
                    user=user,
                    article=article,
                    is_read=True,
                    read_at=now.subtract(days=i).to_datetime_string()
                )
        
        # Test unread count calculation
        unread_score = calculator._calculate_unread_score(feed)
        
        # Should have 7 unread articles, normalized to 0-1 scale
        expected_unread = 7
        assert unread_score > 0.6  # High unread count should give high score
        
    def test_posting_frequency_scoring(self, sample_data):
        """Test posting frequency factor calculation"""
        user = sample_data['user']
        feed = sample_data['feeds']['high']
        calculator = FeedPriorityCalculator(user)
        
        # Create posting history - daily posts (high frequency)
        today = pendulum.now().date()
        for i in range(7):  # 7 days of history
            FeedPostingHistory.create(
                feed=feed,
                posting_date=today - timedelta(days=i),
                articles_count=2,  # 2 articles per day
                created_at=pendulum.now().to_datetime_string()
            )
        
        # Test posting frequency calculation
        frequency_score = calculator._calculate_posting_frequency_score(feed)
        
        # Daily posting should give high score (frequent updates)
        assert frequency_score > 0.7
        
        # Update feed with calculated frequency
        feed.posting_frequency_days = 1.0  # Daily posting
        feed.save()
        
        # Test again with stored frequency
        frequency_score2 = calculator._calculate_posting_frequency_score(feed)
        assert frequency_score2 > 0.7
    
    def test_user_engagement_scoring(self, sample_data):
        """Test user engagement factor calculation"""
        user = sample_data['user']
        feed = sample_data['feeds']['high']
        calculator = FeedPriorityCalculator(user)
        
        # Create articles and reading history
        now = pendulum.now()
        for i in range(20):
            article = Article.create(
                feed=feed,
                title=f"Article {i}",
                url=f"https://example.com/article-{i}",
                guid=f"article-{i}",
                published_date=now.subtract(days=i).to_datetime_string()
            )
            
            # High engagement - read most articles
            if i < 15:  # Read 15 out of 20
                ReadStatus.create(
                    user=user,
                    article=article,
                    is_read=True,
                    read_at=now.subtract(days=i).to_datetime_string()
                )
                
                # Some articles also starred
                if i < 5:
                    read_status = ReadStatus.get(
                        (ReadStatus.user == user) & (ReadStatus.article == article)
                    )
                    read_status.is_starred = True
                    read_status.save()
        
        engagement_score = calculator._calculate_user_engagement_score(feed)
        
        # High read percentage + stars should give high engagement score
        assert engagement_score > 0.6
    
    def test_read_percentage_scoring(self, sample_data):
        """Test read percentage factor calculation"""
        user = sample_data['user']
        feed = sample_data['feeds']['high']
        calculator = FeedPriorityCalculator(user)
        
        # Create articles with specific read pattern
        now = pendulum.now()
        for i in range(10):
            article = Article.create(
                feed=feed,
                title=f"Article {i}",
                url=f"https://example.com/article-{i}",
                guid=f"article-{i}",
                published_date=now.subtract(days=i).to_datetime_string()
            )
            
            # Read 8 out of 10 articles (80% read rate)
            if i < 8:
                ReadStatus.create(
                    user=user,
                    article=article,
                    is_read=True,
                    read_at=now.subtract(days=i).to_datetime_string()
                )
        
        read_percentage_score = calculator._calculate_read_percentage_score(feed)
        
        # 80% read rate should give good score
        assert 0.7 < read_percentage_score < 0.9
    
    def test_combined_priority_calculation(self, sample_data):
        """Test the complete priority calculation with all factors"""
        user = sample_data['user']
        high_feed = sample_data['feeds']['high']
        low_feed = sample_data['feeds']['low']
        calculator = FeedPriorityCalculator(user)
        
        # Set up high priority feed
        now = pendulum.now()
        
        # High unread count
        for i in range(15):
            article = Article.create(
                feed=high_feed,
                title=f"High Priority Article {i}",
                url=f"https://high.com/article-{i}",
                guid=f"high-article-{i}",
                published_date=now.subtract(days=i).to_datetime_string()
            )
            # Only mark a few as read (high unread count)
            if i < 3:
                ReadStatus.create(
                    user=user,
                    article=article,
                    is_read=True,
                    read_at=now.subtract(days=i).to_datetime_string()
                )
        
        # High posting frequency
        for i in range(7):
            FeedPostingHistory.create(
                feed=high_feed,
                posting_date=now.date() - timedelta(days=i),
                articles_count=3,
                created_at=now.to_datetime_string()
            )
        
        # Set up low priority feed  
        # Low unread count
        for i in range(5):
            article = Article.create(
                feed=low_feed,
                title=f"Low Priority Article {i}",
                url=f"https://low.com/article-{i}",
                guid=f"low-article-{i}",
                published_date=now.subtract(days=i*3).to_datetime_string()  # Older articles
            )
            # Mark most as read (low unread count)
            if i < 4:
                ReadStatus.create(
                    user=user,
                    article=article,
                    is_read=True,
                    read_at=now.subtract(days=i*3).to_datetime_string()
                )
        
        # Low posting frequency
        FeedPostingHistory.create(
            feed=low_feed,
            posting_date=now.date() - timedelta(days=7),
            articles_count=1,
            created_at=now.to_datetime_string()
        )
        
        # Calculate priorities
        high_priority = calculator.calculate_priority(high_feed)
        low_priority = calculator.calculate_priority(low_feed)
        
        # High priority feed should score higher than low priority feed
        assert high_priority > low_priority
        assert high_priority > 0.5
        assert low_priority < 0.5
    
    def test_priority_caching(self, sample_data):
        """Test priority score caching mechanism"""
        user = sample_data['user']
        feed = sample_data['feeds']['high']
        calculator = FeedPriorityCalculator(user)
        
        # Create some data
        article = Article.create(
            feed=feed,
            title="Test Article",
            url="https://example.com/test",
            guid="test-article",
            published_date=pendulum.now().to_datetime_string()
        )
        
        # Calculate priority and verify it's cached
        priority1 = calculator.calculate_priority(feed)
        assert priority1 >= 0.0
        
        # Verify the score was saved to the feed
        feed.refresh()  # Reload from database
        assert feed.priority_score == priority1
        
        # Calculate again - should return cached value quickly
        priority2 = calculator.calculate_priority(feed, use_cache=True)
        assert priority2 == priority1
    
    def test_priority_scoring_edge_cases(self, temp_db):
        """Test edge cases in priority scoring"""
        user = User.create(username="testuser")
        category = Category.create(name="Test Category")
        calculator = FeedPriorityCalculator(user)
        
        # Test feed with no articles
        empty_feed = Feed.create(
            url="https://empty.com/feed.xml",
            title="Empty Feed",
            category=category
        )
        
        empty_priority = calculator.calculate_priority(empty_feed)
        assert 0.0 <= empty_priority <= 1.0  # Should handle gracefully
        
        # Test feed with no posting history
        no_history_feed = Feed.create(
            url="https://no-history.com/feed.xml",
            title="No History Feed", 
            category=category
        )
        
        no_history_priority = calculator.calculate_priority(no_history_feed)
        assert 0.0 <= no_history_priority <= 1.0
        
        # Test inactive feed
        inactive_feed = Feed.create(
            url="https://inactive.com/feed.xml",
            title="Inactive Feed",
            category=category,
            is_active=False
        )
        
        inactive_priority = calculator.calculate_priority(inactive_feed)
        assert inactive_priority == 0.0  # Inactive feeds should get 0 priority
    
    def test_bulk_priority_calculation(self, sample_data):
        """Test calculating priorities for multiple feeds efficiently"""
        user = sample_data['user']
        feeds = list(sample_data['feeds'].values())
        calculator = FeedPriorityCalculator(user)
        
        # Add some articles to make calculation meaningful
        now = pendulum.now()
        for feed in feeds:
            for i in range(5):
                Article.create(
                    feed=feed,
                    title=f"Article {i} for {feed.title}",
                    url=f"{feed.url}#article-{i}",
                    guid=f"{feed.id}-article-{i}",
                    published_date=now.subtract(days=i).to_datetime_string()
                )
        
        # Calculate priorities for all feeds
        priorities = calculator.calculate_priorities_bulk(feeds)
        
        assert len(priorities) == len(feeds)
        for feed_id, priority in priorities.items():
            assert 0.0 <= priority <= 1.0
        
        # Verify scores were cached in database
        for feed in feeds:
            feed.refresh()
            assert feed.priority_score >= 0.0