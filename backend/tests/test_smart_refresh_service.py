"""
Tests for SmartRefreshService - Sequential feed refresh with priority ordering
"""
import pytest
import tempfile
import os
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import pendulum

from app.core.database import db, init_database
from app.models.base import Feed, Category, RefreshMetrics
from app.models.article import User, Article
from app.services.smart_refresh_service import SmartRefreshService, RefreshProgress
from app.services.priority_calculator import FeedPriorityCalculator


class TestSmartRefreshService:
    """Test the smart refresh service with priority-based ordering"""
    
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
    def sample_feeds(self, temp_db):
        """Create sample feeds for testing"""
        # Create user and category
        timestamp = str(pendulum.now().timestamp()).replace('.', '')
        user = User.create(
            username='smart_refresh_test_' + timestamp,
            email='smartrefresh' + timestamp + '@example.com',
            password_hash='test_hash',
            auto_refresh_feeds=True
        )
        
        category = Category.create(name='Smart Refresh Test Category')
        
        # Create feeds with different priorities
        high_priority_feed = Feed.create(
            url=f'https://high-priority-{timestamp}.com/feed.xml',
            title='High Priority Feed',
            category=category,
            is_active=True,
            priority_score=0.9
        )
        
        medium_priority_feed = Feed.create(
            url=f'https://medium-priority-{timestamp}.com/feed.xml',
            title='Medium Priority Feed',
            category=category,
            is_active=True,
            priority_score=0.5
        )
        
        low_priority_feed = Feed.create(
            url=f'https://low-priority-{timestamp}.com/feed.xml',
            title='Low Priority Feed',
            category=category,
            is_active=True,
            priority_score=0.1
        )
        
        inactive_feed = Feed.create(
            url=f'https://inactive-{timestamp}.com/feed.xml',
            title='Inactive Feed',
            category=category,
            is_active=False,
            priority_score=0.8
        )
        
        return {
            'user': user,
            'category': category,
            'feeds': {
                'high': high_priority_feed,
                'medium': medium_priority_feed,
                'low': low_priority_feed,
                'inactive': inactive_feed
            }
        }
    
    def test_service_initialization(self, temp_db):
        """Test SmartRefreshService can be initialized"""
        timestamp = str(pendulum.now().timestamp()).replace('.', '')
        user = User.create(
            username='init_test_' + timestamp,
            email='init' + timestamp + '@example.com',
            password_hash='test_hash'
        )
        
        service = SmartRefreshService(user)
        
        assert service.user.id == user.id
        assert service.batch_size == 5  # Default batch size
        assert service.delay_between_feeds == 2.0  # Default delay
        assert service.max_retries == 3  # Default max retries
        assert service.progress is None  # No active refresh
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self, sample_feeds):
        """Test that feeds are processed in priority order"""
        user = sample_feeds['user']
        feeds = sample_feeds['feeds']
        service = SmartRefreshService(user)
        
        # Mock the feed refresh functionality
        with patch('app.services.feed_fetcher.feed_fetcher.update_multiple_feeds') as mock_refresh:
            # Mock successful refresh results
            mock_refresh.return_value = [
                MagicMock(success=True, articles_added=2, feed_id=feeds['high'].id),
                MagicMock(success=True, articles_added=1, feed_id=feeds['medium'].id),
                MagicMock(success=True, articles_added=0, feed_id=feeds['low'].id),
            ]
            
            # Start refresh
            progress = await service.refresh_feeds_by_priority()
            
            # Verify feeds were processed in priority order
            assert progress.total_feeds == 3  # Only active feeds
            assert progress.completed_feeds == 3
            assert progress.successful_refreshes == 3
            assert progress.failed_refreshes == 0
            
            # Verify inactive feed was not processed
            processed_feed_ids = [call.args[0][0].id for call in mock_refresh.call_args_list]
            assert feeds['inactive'].id not in processed_feed_ids
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, sample_feeds):
        """Test configurable batch processing"""
        user = sample_feeds['user']
        service = SmartRefreshService(user, batch_size=2)  # Process 2 feeds at a time
        
        with patch('app.services.feed_fetcher.feed_fetcher.update_multiple_feeds') as mock_refresh:
            mock_refresh.return_value = [
                MagicMock(success=True, articles_added=1, feed_id=1),
                MagicMock(success=True, articles_added=1, feed_id=2),
            ]
            
            progress = await service.refresh_feeds_by_priority()
            
            # Should have made 2 calls (batch_size=2, 3 active feeds = 2 batches)
            assert mock_refresh.call_count == 2
            
            # First batch should have 2 feeds, second batch should have 1 feed
            first_batch_size = len(mock_refresh.call_args_list[0].args[0])
            second_batch_size = len(mock_refresh.call_args_list[1].args[0])
            
            assert first_batch_size == 2
            assert second_batch_size == 1
    
    @pytest.mark.asyncio
    async def test_error_handling_with_backoff(self, sample_feeds):
        """Test individual feed error handling with exponential backoff"""
        user = sample_feeds['user']
        feeds = sample_feeds['feeds']
        service = SmartRefreshService(user, max_retries=2)
        
        # Mock feed fetcher to fail on first feed, succeed on others
        with patch('app.services.feed_fetcher.feed_fetcher.update_multiple_feeds') as mock_refresh:
            def mock_refresh_func(feed_list, **kwargs):
                results = []
                for feed in feed_list:
                    if feed.id == feeds['high'].id:
                        # First feed fails
                        results.append(MagicMock(
                            success=False, 
                            error_message="Connection timeout",
                            feed_id=feed.id
                        ))
                    else:
                        # Other feeds succeed
                        results.append(MagicMock(
                            success=True,
                            articles_added=1,
                            feed_id=feed.id
                        ))
                return results
            
            mock_refresh.side_effect = mock_refresh_func
            
            progress = await service.refresh_feeds_by_priority()
            
            # Verify error handling
            assert progress.failed_refreshes == 1  # High priority feed failed
            assert progress.successful_refreshes == 2  # Medium and low succeeded
            assert progress.errors[feeds['high'].id]['count'] == 1
            assert "Connection timeout" in progress.errors[feeds['high'].id]['last_error']
    
    @pytest.mark.asyncio
    async def test_refresh_progress_tracking(self, sample_feeds):
        """Test refresh progress tracking and status reporting"""
        user = sample_feeds['user']
        service = SmartRefreshService(user)
        
        with patch('app.services.feed_fetcher.feed_fetcher.update_multiple_feeds') as mock_refresh:
            # Mock slow refresh to test progress tracking
            async def slow_refresh(feed_list, **kwargs):
                await asyncio.sleep(0.1)  # Simulate processing time
                return [MagicMock(success=True, articles_added=1, feed_id=feed.id) for feed in feed_list]
            
            mock_refresh.side_effect = slow_refresh
            
            # Start refresh in background
            refresh_task = asyncio.create_task(service.refresh_feeds_by_priority())
            
            # Check progress while refresh is running
            await asyncio.sleep(0.05)  # Let refresh start
            
            current_progress = service.get_refresh_progress()
            assert current_progress is not None
            assert current_progress.is_active
            assert current_progress.started_at is not None
            
            # Wait for completion
            final_progress = await refresh_task
            
            assert not final_progress.is_active
            assert final_progress.completed_at is not None
            assert final_progress.duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_metrics_recording(self, sample_feeds):
        """Test that refresh metrics are recorded"""
        user = sample_feeds['user']
        service = SmartRefreshService(user)
        
        with patch('app.services.feed_fetcher.feed_fetcher.update_multiple_feeds') as mock_refresh:
            mock_refresh.return_value = [
                MagicMock(success=True, articles_added=2, feed_id=1),
                MagicMock(success=True, articles_added=1, feed_id=2),
                MagicMock(success=True, articles_added=0, feed_id=3),
            ]
            
            progress = await service.refresh_feeds_by_priority()
            
            # Check that metrics were recorded
            metrics = RefreshMetrics.select().order_by(RefreshMetrics.created_at.desc()).first()
            
            assert metrics is not None
            assert metrics.feeds_processed == 3
            assert metrics.batch_size == service.batch_size
            assert metrics.total_duration_seconds > 0
            assert metrics.priority_algorithm_version == 'v1.0'
    
    @pytest.mark.asyncio
    async def test_consecutive_failure_tracking(self, sample_feeds):
        """Test tracking of consecutive failures for feeds"""
        user = sample_feeds['user']
        feeds = sample_feeds['feeds']
        service = SmartRefreshService(user)
        
        # Initial failure counts should be 0
        assert feeds['high'].consecutive_failures == 0
        
        with patch('app.services.feed_fetcher.feed_fetcher.update_multiple_feeds') as mock_refresh:
            # Mock feed to fail consistently
            mock_refresh.return_value = [
                MagicMock(success=False, error_message="Feed not found", feed_id=feeds['high'].id),
                MagicMock(success=True, articles_added=1, feed_id=feeds['medium'].id),
            ]
            
            # Run refresh twice
            await service.refresh_feeds_by_priority()
            await service.refresh_feeds_by_priority()
            
            # Check consecutive failure tracking
            feeds['high'].refresh()  # Reload from database
            feeds['medium'].refresh()
            
            assert feeds['high'].consecutive_failures == 2
            assert feeds['medium'].consecutive_failures == 0  # Successful feed resets count
    
    @pytest.mark.asyncio
    async def test_delay_between_feeds(self, sample_feeds):
        """Test configurable delay between feed processing"""
        user = sample_feeds['user']
        service = SmartRefreshService(user, delay_between_feeds=0.1, batch_size=1)  # Short delay for testing
        
        with patch('app.services.feed_fetcher.feed_fetcher.update_multiple_feeds') as mock_refresh:
            mock_refresh.return_value = [MagicMock(success=True, articles_added=1, feed_id=1)]
            
            start_time = asyncio.get_event_loop().time()
            await service.refresh_feeds_by_priority()
            end_time = asyncio.get_event_loop().time()
            
            # Should take at least delay_time * (number_of_batches - 1) 
            # 3 feeds, batch_size=1 = 3 batches, 2 delays = 0.2 seconds minimum
            assert (end_time - start_time) >= 0.15  # Allow some margin for processing
    
    def test_refresh_progress_model(self, temp_db):
        """Test RefreshProgress model functionality"""
        progress = RefreshProgress(
            refresh_id="test-refresh-123",
            user_id=1,
            total_feeds=10
        )
        
        # Test initial state
        assert not progress.is_active
        assert progress.completed_feeds == 0
        assert progress.successful_refreshes == 0
        assert progress.failed_refreshes == 0
        
        # Test starting refresh
        progress.start()
        assert progress.is_active
        assert progress.started_at is not None
        
        # Test updating progress
        progress.update_progress(completed=3, successful=2, failed=1)
        assert progress.completed_feeds == 3
        assert progress.successful_refreshes == 2
        assert progress.failed_refreshes == 1
        
        # Test adding errors
        progress.add_error(feed_id=5, error_message="Connection failed")
        assert 5 in progress.errors
        assert progress.errors[5]['count'] == 1
        assert "Connection failed" in progress.errors[5]['last_error']
        
        # Test completing refresh
        progress.complete()
        assert not progress.is_active
        assert progress.completed_at is not None
        assert progress.duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_priority_recalculation_during_refresh(self, sample_feeds):
        """Test that priorities can be recalculated during refresh process"""
        user = sample_feeds['user']
        feeds = sample_feeds['feeds']
        service = SmartRefreshService(user, recalculate_priorities=True)
        
        with patch('app.services.feed_fetcher.feed_fetcher.update_multiple_feeds') as mock_refresh:
            with patch.object(FeedPriorityCalculator, 'calculate_priorities_bulk') as mock_priority_calc:
                # Mock priority recalculation
                mock_priority_calc.return_value = {
                    feeds['high'].id: 0.95,
                    feeds['medium'].id: 0.6,
                    feeds['low'].id: 0.2
                }
                
                mock_refresh.return_value = [
                    MagicMock(success=True, articles_added=1, feed_id=1)
                ]
                
                await service.refresh_feeds_by_priority()
                
                # Verify priorities were recalculated
                mock_priority_calc.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_cancellation(self, sample_feeds):
        """Test that refresh can be cancelled mid-process"""
        user = sample_feeds['user']
        service = SmartRefreshService(user, delay_between_feeds=1.0)  # Long delay
        
        with patch('app.services.feed_fetcher.feed_fetcher.update_multiple_feeds') as mock_refresh:
            async def slow_refresh(feed_list, **kwargs):
                await asyncio.sleep(2.0)  # Very slow refresh
                return [MagicMock(success=True, articles_added=1, feed_id=feed.id) for feed in feed_list]
            
            mock_refresh.side_effect = slow_refresh
            
            # Start refresh
            refresh_task = asyncio.create_task(service.refresh_feeds_by_priority())
            
            # Cancel after short delay
            await asyncio.sleep(0.1)
            service.cancel_refresh()
            
            # Verify refresh was cancelled
            try:
                result = await refresh_task
                # If we get here, check that refresh was marked as cancelled
                assert result.cancelled == True
            except asyncio.CancelledError:
                # This is also acceptable
                pass
    
    @pytest.mark.asyncio
    async def test_empty_feed_list_handling(self, temp_db):
        """Test handling of empty feed list"""
        timestamp = str(pendulum.now().timestamp()).replace('.', '')
        user = User.create(
            username='empty_test_' + timestamp,
            email='empty' + timestamp + '@example.com',
            password_hash='test_hash'
        )
        
        service = SmartRefreshService(user)
        
        # Test with no feeds
        progress = await service.refresh_feeds_by_priority()
        
        assert progress.total_feeds == 0
        assert progress.completed_feeds == 0
        assert not progress.is_active
        assert progress.duration_seconds >= 0
    
    @pytest.mark.asyncio
    async def test_refresh_status_persistence(self, sample_feeds):
        """Test that refresh status can be retrieved after completion"""
        user = sample_feeds['user']
        service = SmartRefreshService(user)
        
        with patch('app.services.feed_fetcher.feed_fetcher.update_multiple_feeds') as mock_refresh:
            mock_refresh.return_value = [
                MagicMock(success=True, articles_added=1, feed_id=1)
            ]
            
            # Start and complete refresh
            progress = await service.refresh_feeds_by_priority()
            refresh_id = progress.refresh_id
            
            # Retrieve status after completion
            retrieved_progress = service.get_refresh_status(refresh_id)
            
            assert retrieved_progress is not None
            assert retrieved_progress.refresh_id == refresh_id
            assert not retrieved_progress.is_active
            assert retrieved_progress.completed_at is not None