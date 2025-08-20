import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import httpx
from datetime import datetime, timedelta

from app.models.base import Feed, Category, FeedCheckLog
from app.services.feed_health_service import FeedHealthService, FeedCheckSession, FeedCheckResult


class TestFeedHealthService:
    """Test suite for FeedHealthService"""
    
    @pytest.fixture
    def sample_feed(self, sample_category):
        """Create a sample feed for testing"""
        return Feed.create(
            url="https://example.com/feed.xml",
            title="Test Feed",
            category=sample_category
        )
    
    @pytest.mark.asyncio
    async def test_check_feed_accessibility_success_200(self, sample_feed):
        """Test successful feed check with 200 status"""
        service = FeedHealthService()
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/rss+xml"}
        
        with patch('httpx.AsyncClient.head', new_callable=AsyncMock) as mock_head:
            mock_head.return_value = mock_response
            
            result = await service.check_feed_accessibility(sample_feed.url)
            
            assert result.success is True
            assert result.status_code == 200
            assert result.error_message is None
            assert result.response_time_ms is not None
            assert result.response_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_check_feed_accessibility_success_301_redirect(self, sample_feed):
        """Test successful feed check with 301 redirect"""
        service = FeedHealthService()
        
        # Mock redirect response
        mock_response = Mock()
        mock_response.status_code = 301
        
        with patch('httpx.AsyncClient.head', new_callable=AsyncMock) as mock_head:
            mock_head.return_value = mock_response
            
            result = await service.check_feed_accessibility(sample_feed.url)
            
            assert result.success is True  # Redirects should be considered successful
            assert result.status_code == 301
            assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_check_feed_accessibility_failure_404(self, sample_feed):
        """Test failed feed check with 404 status"""
        service = FeedHealthService()
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient.head', new_callable=AsyncMock) as mock_head:
            mock_head.return_value = mock_response
            
            result = await service.check_feed_accessibility(sample_feed.url)
            
            assert result.success is False
            assert result.status_code == 404
            assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_check_feed_accessibility_timeout(self, sample_feed):
        """Test feed check with timeout error"""
        service = FeedHealthService()
        
        with patch('httpx.AsyncClient.head', new_callable=AsyncMock) as mock_head:
            mock_head.side_effect = httpx.TimeoutException("Request timed out")
            
            result = await service.check_feed_accessibility(sample_feed.url)
            
            assert result.success is False
            assert result.status_code is None
            assert "timed out" in result.error_message.lower()
            assert result.response_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_check_feed_accessibility_connection_error(self, sample_feed):
        """Test feed check with connection error"""
        service = FeedHealthService()
        
        with patch('httpx.AsyncClient.head', new_callable=AsyncMock) as mock_head:
            mock_head.side_effect = httpx.ConnectError("Connection failed")
            
            result = await service.check_feed_accessibility(sample_feed.url)
            
            assert result.success is False
            assert result.status_code is None
            assert "connection" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_check_feed_accessibility_ssl_error(self, sample_feed):
        """Test feed check with SSL error"""
        service = FeedHealthService()
        
        with patch('httpx.AsyncClient.head', new_callable=AsyncMock) as mock_head:
            mock_head.side_effect = httpx.ConnectError("SSL: CERTIFICATE_VERIFY_FAILED")
            
            result = await service.check_feed_accessibility(sample_feed.url)
            
            assert result.success is False
            assert result.status_code is None
            assert "ssl" in result.error_message.lower() or "certificate" in result.error_message.lower()
    
    def test_update_feed_status_accessible_to_inaccessible(self, sample_feed):
        """Test updating feed from accessible to inaccessible"""
        service = FeedHealthService()
        
        # Feed starts as accessible
        assert sample_feed.accessible is True
        assert sample_feed.consecutive_failures == 0
        
        # Mock failed check result
        failed_result = FeedCheckResult(
            success=False,
            status_code=404,
            error_message="Not Found",
            response_time_ms=1000
        )
        
        service.update_feed_status(sample_feed, failed_result)
        
        # Reload from database
        updated_feed = Feed.get_by_id(sample_feed.id)
        assert updated_feed.accessible is False
        assert updated_feed.consecutive_failures == 1
        assert updated_feed.last_checked is not None
    
    def test_update_feed_status_consecutive_failures_increment(self, sample_feed):
        """Test that consecutive failures are incremented correctly"""
        service = FeedHealthService()
        
        # Set feed as already having some failures
        sample_feed.accessible = False
        sample_feed.consecutive_failures = 5
        sample_feed.save()
        
        failed_result = FeedCheckResult(
            success=False,
            status_code=500,
            error_message="Server Error",
            response_time_ms=2000
        )
        
        service.update_feed_status(sample_feed, failed_result)
        
        updated_feed = Feed.get_by_id(sample_feed.id)
        assert updated_feed.consecutive_failures == 6
        assert updated_feed.accessible is False
    
    def test_update_feed_status_reset_failures_on_success(self, sample_feed):
        """Test that consecutive failures reset on successful check"""
        service = FeedHealthService()
        
        # Set feed as having previous failures
        sample_feed.accessible = False
        sample_feed.consecutive_failures = 10
        sample_feed.save()
        
        success_result = FeedCheckResult(
            success=True,
            status_code=200,
            response_time_ms=800
        )
        
        service.update_feed_status(sample_feed, success_result)
        
        updated_feed = Feed.get_by_id(sample_feed.id)
        assert updated_feed.accessible is True
        assert updated_feed.consecutive_failures == 0
    
    def test_log_feed_check_result(self, sample_feed):
        """Test logging of feed check result"""
        service = FeedHealthService()
        
        check_result = FeedCheckResult(
            success=True,
            status_code=200,
            response_time_ms=850
        )
        
        service.log_feed_check_result(sample_feed, check_result)
        
        # Verify log was created
        logs = FeedCheckLog.select().where(FeedCheckLog.feed == sample_feed)
        assert logs.count() == 1
        
        log = logs.get()
        assert log.is_success is True
        assert log.status_code == 200
        assert log.response_time_ms == 850
        assert log.error_message is None


class TestFeedCheckSession:
    """Test suite for FeedCheckSession"""
    
    def test_session_creation_with_feed_ids(self, sample_category):
        """Test session creation with feed IDs"""
        feed_ids = [1, 2, 3, 4, 5]
        session = FeedCheckSession("test-session", sample_category.id, feed_ids)
        
        assert session.session_id == "test-session"
        assert session.category_id == sample_category.id
        assert session.feed_ids == feed_ids
        assert session.completed == 0
        assert session.status == "pending"
        assert session.results["accessible"] == 0
        assert session.results["inaccessible"] == 0
    
    def test_session_progress_tracking(self, sample_category):
        """Test session progress tracking"""
        feed_ids = [1, 2, 3]
        session = FeedCheckSession("test-session", sample_category.id, feed_ids)
        
        # Start session
        session.start()
        assert session.status == "running"
        
        # Update progress
        session.update_progress(accessible=True)
        assert session.completed == 1
        assert session.results["accessible"] == 1
        assert session.results["inaccessible"] == 0
        
        session.update_progress(accessible=False)
        assert session.completed == 2
        assert session.results["accessible"] == 1
        assert session.results["inaccessible"] == 1
        
        # Complete session
        session.update_progress(accessible=True)
        assert session.completed == 3
        assert session.status == "completed"
    
    def test_session_completion_status(self, sample_category):
        """Test that session completes when all feeds processed"""
        feed_ids = [1, 2]
        session = FeedCheckSession("test-session", sample_category.id, feed_ids)
        
        session.start()
        assert session.status == "running"
        assert not session.is_complete()
        
        session.update_progress(accessible=True)
        assert not session.is_complete()
        
        session.update_progress(accessible=False)
        assert session.is_complete()
        assert session.status == "completed"
    
    def test_session_error_handling(self, sample_category):
        """Test session error handling"""
        feed_ids = [1, 2, 3]
        session = FeedCheckSession("test-session", sample_category.id, feed_ids)
        
        session.start()
        
        # Simulate error during processing
        session.add_error("Failed to check feed 2: Connection timeout")
        
        # Session should still continue
        assert session.status == "running"
        assert len(session.errors) == 1
        assert "Connection timeout" in session.errors[0]
    
    @pytest.mark.asyncio
    async def test_session_concurrent_feed_checking(self, sample_category):
        """Test concurrent processing of multiple feeds"""
        # Create test feeds
        feeds = []
        for i in range(3):
            feed = Feed.create(
                url=f"https://example{i}.com/feed.xml",
                title=f"Test Feed {i}",
                category=sample_category
            )
            feeds.append(feed)
        
        feed_ids = [f.id for f in feeds]
        session = FeedCheckSession("test-session", sample_category.id, feed_ids)
        service = FeedHealthService()
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.head', new_callable=AsyncMock) as mock_head:
            mock_head.return_value = mock_response
            
            session.start()
            
            # Process all feeds concurrently
            tasks = []
            for feed in feeds:
                task = service.check_and_update_feed(feed, session)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            assert session.is_complete()
            assert session.results["accessible"] == 3
            assert session.results["inaccessible"] == 0