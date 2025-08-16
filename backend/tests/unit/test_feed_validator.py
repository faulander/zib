import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import aiohttp
import feedparser
from aioresponses import aioresponses
from app.services.opml.validator import (
    FeedValidator, 
    FeedValidationResult,
    FeedValidationError
)
from app.models.base import ImportFeedValidation
from app.core.database import db


class TestFeedValidator:
    '''Test feed validation functionality'''
    
    @pytest.fixture
    def validator(self):
        '''Create a feed validator instance'''
        return FeedValidator()
    
    
    @pytest.fixture
    def valid_rss_content(self):
        '''Valid RSS feed content'''
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Example Feed</title>
                <link>https://example.com</link>
                <description>An example RSS feed</description>
                <language>en-US</language>
                <item>
                    <title>First Post</title>
                    <link>https://example.com/post1</link>
                    <description>This is the first post</description>
                </item>
            </channel>
        </rss>'''
    
    @pytest.fixture
    def valid_atom_content(self):
        '''Valid Atom feed content'''
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Example Atom Feed</title>
            <link href="https://example.com/"/>
            <subtitle>An example Atom feed</subtitle>
            <id>https://example.com/feed</id>
            <entry>
                <title>First Entry</title>
                <link href="https://example.com/entry1"/>
                <summary>This is the first entry</summary>
            </entry>
        </feed>'''
    
    @pytest.mark.asyncio
    async def test_validate_valid_rss_feed(self, validator, valid_rss_content):
        '''Test validation of a valid RSS feed'''
        with aioresponses() as m:
            # Mock HTTP response
            m.get('https://example.com/feed', 
                  status=200,
                  body=valid_rss_content,
                  headers={'content-type': 'application/rss+xml'})
            
            with patch('app.services.opml.validator.feedparser.parse') as mock_parse:
                # Create a mock feedparser result with attributes
                mock_result = Mock()
                mock_result.bozo = False
                mock_result.version = 'rss20'
                mock_result.feed = {
                    'title': 'Example Feed',
                    'link': 'https://example.com',
                    'subtitle': 'An example RSS feed',
                    'language': 'en-US'
                }
                mock_parse.return_value = mock_result
                
                result = await validator.validate_feed('https://example.com/feed', use_cache=False)
        
        assert result.is_valid is True
        assert result.feed_url == 'https://example.com/feed'
        assert result.final_url == 'https://example.com/feed'
        assert result.title == 'Example Feed'
        assert result.description == 'An example RSS feed'
        assert result.feed_type == 'rss'
        assert result.language == 'en-US'
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_validate_valid_atom_feed(self, validator, valid_atom_content):
        '''Test validation of a valid Atom feed'''
        with aioresponses() as m:
            # Mock HTTP response
            m.get('https://example.com/atom', 
                  status=200,
                  body=valid_atom_content,
                  headers={'content-type': 'application/atom+xml'})
            
            with patch('app.services.opml.validator.feedparser.parse') as mock_parse:
                # Create a mock feedparser result with attributes
                mock_result = Mock()
                mock_result.bozo = False
                mock_result.version = 'atom10'
                mock_result.feed = {
                    'title': 'Example Atom Feed',
                    'link': 'https://example.com/',
                    'subtitle': 'An example Atom feed'
                }
                mock_parse.return_value = mock_result
                
                result = await validator.validate_feed('https://example.com/atom', use_cache=False)
        
        assert result.is_valid is True
        assert result.feed_type == 'atom'
        assert result.title == 'Example Atom Feed'
    
    @pytest.mark.asyncio
    async def test_validate_with_redirect(self, validator):
        '''Test handling of HTTP redirects'''
        with aioresponses() as m:
            # Mock HTTP redirect
            m.get('https://example.com/oldfeed',
                  status=301,
                  headers={'Location': 'https://example.com/newfeed'})
            m.get('https://example.com/newfeed', 
                  status=200,
                  body='<rss></rss>',
                  headers={'content-type': 'application/rss+xml'})
            
            with patch('app.services.opml.validator.feedparser.parse') as mock_parse:
                # Create a mock feedparser result with attributes
                mock_result = Mock()
                mock_result.bozo = False
                mock_result.version = 'rss20'
                mock_result.feed = {'title': 'Redirected Feed'}
                mock_parse.return_value = mock_result
                
                result = await validator.validate_feed('https://example.com/oldfeed', use_cache=False)
        
        # Note: aiohttp follows redirects automatically, so final_url will be the redirected URL
        assert result.is_valid is True
        assert result.feed_url == 'https://example.com/oldfeed'
        # The final_url will be the redirected URL due to aiohttp's automatic redirect following
        assert result.final_url == 'https://example.com/newfeed'
    
    @pytest.mark.asyncio
    async def test_validate_404_error(self, validator):
        '''Test handling of 404 Not Found'''
        with aioresponses() as m:
            # Mock 404 response
            m.get('https://example.com/missing', 
                  status=404,
                  reason='Not Found')
            
            result = await validator.validate_feed('https://example.com/missing', use_cache=False)
        
        assert result.is_valid is False
        assert result.error_code == '404'
        assert 'Not Found' in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_network_error(self, validator):
        '''Test handling of network errors'''
        with aioresponses() as m:
            # Mock network error
            m.get('https://example.com/feed', 
                  exception=aiohttp.ClientError('Connection failed'))
            
            result = await validator.validate_feed('https://example.com/feed', use_cache=False)
        
        assert result.is_valid is False
        assert result.error_code == 'network_error'
        assert 'Connection failed' in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_timeout(self, validator):
        '''Test handling of timeout errors'''
        with aioresponses() as m:
            # Mock timeout error
            m.get('https://example.com/feed', 
                  exception=asyncio.TimeoutError())
            
            result = await validator.validate_feed('https://example.com/feed', use_cache=False)
        
        assert result.is_valid is False
        assert result.error_code == 'timeout'
        assert 'timeout' in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_invalid_feed_content(self, validator):
        '''Test handling of invalid feed content'''
        with aioresponses() as m:
            # Mock HTTP response with invalid content
            m.get('https://example.com/notfeed',
                  status=200,
                  body='<html><body>Not a feed</body></html>',
                  headers={'content-type': 'text/html'})  # Wrong content type
            
            with patch('app.services.opml.validator.feedparser.parse') as mock_parse:
                # Create a mock feedparser result with bozo error
                mock_result = Mock()
                mock_result.bozo = True
                mock_result.bozo_exception = Exception('Not a valid feed')
                mock_parse.return_value = mock_result
                
                result = await validator.validate_feed('https://example.com/notfeed', use_cache=False)
        
        assert result.is_valid is False
        assert result.error_code == 'invalid_feed'
        assert 'Not a valid feed' in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_with_user_agent(self, validator):
        '''Test that proper User-Agent is sent'''
        with aioresponses() as m:
            # Mock HTTP response
            m.get('https://example.com/feed',
                  status=200,
                  body='<rss></rss>',
                  headers={'content-type': 'application/rss+xml'})
            
            with patch('app.services.opml.validator.feedparser.parse') as mock_parse:
                # Create a mock feedparser result
                mock_result = Mock()
                mock_result.bozo = False
                mock_result.version = 'rss20'
                mock_result.feed = {}
                mock_parse.return_value = mock_result
                
                await validator.validate_feed('https://example.com/feed', use_cache=False)
            
            # Check that User-Agent header was set
            # aioresponses stores requests differently - let's check the format
            requests = list(m.requests.keys())
            assert len(requests) == 1
            
            # The request key contains method and URL info
            request_key = requests[0]
            # The call history is available as well
            call_info = m.requests[request_key]
            assert len(call_info) == 1
            
            # Extract the call kwargs
            call_kwargs = call_info[0].kwargs
            assert 'headers' in call_kwargs
            assert 'User-Agent' in call_kwargs['headers']
            assert 'Zib RSS Reader' in call_kwargs['headers']['User-Agent']
    
    @pytest.mark.asyncio
    async def test_validate_batch_feeds(self, validator):
        '''Test batch validation of multiple feeds'''
        feed_urls = [
            'https://example.com/feed1',
            'https://example.com/feed2',
            'https://example.com/feed3'
        ]
        
        with aioresponses() as m:
            # Mock responses for each feed
            for i, url in enumerate(feed_urls, 1):
                m.get(url,
                      status=200,
                      body=f'<rss><channel><title>Feed {i}</title></channel></rss>',
                      headers={'content-type': 'application/rss+xml'})
            
            with patch('app.services.opml.validator.feedparser.parse') as mock_parse:
                def parse_side_effect(content):
                    # Extract feed number from content
                    import re
                    match = re.search(r'Feed (\d+)', content)
                    num = match.group(1) if match else '?'
                    
                    # Create a mock feedparser result
                    mock_result = Mock()
                    mock_result.bozo = False
                    mock_result.version = 'rss20'
                    mock_result.feed = {'title': f'Feed {num}'}
                    return mock_result
                
                mock_parse.side_effect = parse_side_effect
                
                results = await validator.validate_batch(feed_urls, use_cache=False)
        
        assert len(results) == 3
        assert all(r.is_valid for r in results)
        assert results[0].title == 'Feed 1'
        assert results[1].title == 'Feed 2'
        assert results[2].title == 'Feed 3'
    
    @pytest.mark.asyncio
    async def test_validation_with_retry(self, validator):
        '''Test retry logic on transient failures'''
        # For retry testing, we'll directly patch the validation method
        # to track retry attempts
        attempts = 0
        original_perform_validation = validator._perform_validation
        
        async def mock_perform_validation(feed_url, session):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise aiohttp.ClientError('Temporary failure')
            
            # Call the original method for the successful attempt
            with aioresponses() as m:
                m.get(feed_url, 
                      status=200,
                      body='<rss></rss>',
                      headers={'content-type': 'application/rss+xml'})
                
                with patch('app.services.opml.validator.feedparser.parse') as mock_parse:
                    # Create a mock feedparser result
                    mock_result = Mock()
                    mock_result.bozo = False
                    mock_result.version = 'rss20'
                    mock_result.feed = {}
                    mock_parse.return_value = mock_result
                    
                    return await original_perform_validation(feed_url, session)
        
        with patch.object(validator, '_perform_validation', new=mock_perform_validation):
            result = await validator.validate_feed('https://example.com/feed', 
                                                  max_retries=3,
                                                  use_cache=False)
        
        assert attempts == 3
        assert result.is_valid is True
    
    @pytest.mark.asyncio
    async def test_validation_cache_hit(self, validator):
        '''Test that cached validation results are returned'''
        # Create a mock cache entry
        cached = FeedValidationResult(
            feed_url='https://example.com/feed',
            is_valid=True,
            final_url='https://example.com/feed',
            title='Cached Feed',
            description='From cache',
            feed_type='rss',
            cached=True
        )
        
        with patch.object(validator, 'get_cached_validation', return_value=cached):
            result = await validator.validate_feed('https://example.com/feed', use_cache=True)
        
        assert result.is_valid is True
        assert result.title == 'Cached Feed'
        assert result.cached is True
    
    @pytest.mark.asyncio
    async def test_validation_cache_miss(self, validator):
        '''Test that cache miss triggers actual validation'''
        with patch.object(validator, 'get_cached_validation', return_value=None):
            with aioresponses() as m:
                # Mock HTTP response
                m.get('https://example.com/feed',
                      status=200,
                      body='<rss></rss>',
                      headers={'content-type': 'application/rss+xml'})
                
                with patch('app.services.opml.validator.feedparser.parse') as mock_parse:
                    # Create a mock feedparser result
                    mock_result = Mock()
                    mock_result.bozo = False
                    mock_result.version = 'rss20'
                    mock_result.feed = {'title': 'Fresh Feed'}
                    mock_parse.return_value = mock_result
                    
                    with patch.object(validator, 'save_to_cache') as mock_save:
                        result = await validator.validate_feed('https://example.com/feed', 
                                                              use_cache=True)
                    
                    # Should save to cache
                    mock_save.assert_called_once()
        
        assert result.is_valid is True
        assert result.title == 'Fresh Feed'
        assert result.cached is False
    
    @pytest.mark.asyncio
    async def test_concurrent_validation_limit(self, validator):
        '''Test that concurrent validations are limited'''
        # Create many feed URLs
        feed_urls = [f'https://example.com/feed{i}' for i in range(20)]
        
        # Track concurrent requests
        concurrent_count = 0
        max_concurrent = 0
        
        with aioresponses() as m:
            # Mock all 20 feeds
            for i in range(20):
                m.get(f'https://example.com/feed{i}',
                      status=200,
                      body='<rss></rss>',
                      headers={'content-type': 'application/rss+xml'})
            
            # Patch the session get method to track concurrency
            original_get = aiohttp.ClientSession.get
            
            async def tracked_get(session_self, url, **kwargs):
                nonlocal concurrent_count, max_concurrent
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
                
                # Simulate some processing time
                await asyncio.sleep(0.01)
                
                try:
                    result = await original_get(session_self, url, **kwargs)
                    return result
                finally:
                    concurrent_count -= 1
            
            with patch('aiohttp.ClientSession.get', new=tracked_get):
                with patch('app.services.opml.validator.feedparser.parse') as mock_parse:
                    # Create a mock feedparser result
                    mock_result = Mock()
                    mock_result.bozo = False
                    mock_result.version = 'rss20'
                    mock_result.feed = {}
                    mock_parse.return_value = mock_result
                    
                    # Validate with concurrency limit
                    results = await validator.validate_batch(feed_urls, 
                                                            max_concurrent=5,
                                                            use_cache=False)
        
        assert len(results) == 20
        assert max_concurrent <= 5  # Should not exceed limit