import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime, timedelta
import feedparser
from aioresponses import aioresponses
from app.services.feed_fetcher import (
    FeedFetcher, FeedFetchResult, FeedUpdateResult, 
    FeedFetchError, FeedParseError
)
from app.models.base import Category, Feed
from app.models.article import Article
from app.core.database import db


@pytest.fixture
def feed_fetcher():
    '''Create FeedFetcher instance'''
    return FeedFetcher(
        timeout=30,
        max_retries=3,
        user_agent='Zib RSS Reader/1.0'
    )


@pytest.fixture
def sample_rss_content():
    '''Sample RSS feed content for testing'''
    return '''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test RSS Feed</title>
            <description>A test RSS feed</description>
            <link>https://example.com</link>
            <lastBuildDate>Mon, 15 Jan 2024 10:30:00 +0000</lastBuildDate>
            
            <item>
                <title>First Article</title>
                <description>Content of the first article</description>
                <link>https://example.com/article-1</link>
                <pubDate>Mon, 15 Jan 2024 10:00:00 +0000</pubDate>
                <guid>article-1-guid</guid>
                <author>john@example.com (John Doe)</author>
                <category>Technology</category>
                <category>Programming</category>
            </item>
            
            <item>
                <title>Second Article</title>
                <description>Content of the second article</description>
                <link>https://example.com/article-2</link>
                <pubDate>Mon, 15 Jan 2024 09:30:00 +0000</pubDate>
                <guid>article-2-guid</guid>
            </item>
        </channel>
    </rss>'''


@pytest.fixture
def sample_atom_content():
    '''Sample Atom feed content for testing'''
    return '''<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Test Atom Feed</title>
        <subtitle>A test Atom feed</subtitle>
        <link href="https://example.com"/>
        <updated>2024-01-15T10:30:00Z</updated>
        <id>https://example.com/atom.xml</id>
        
        <entry>
            <title>Atom Article 1</title>
            <content type="html">HTML content of the first atom article</content>
            <link href="https://example.com/atom-1"/>
            <updated>2024-01-15T10:00:00Z</updated>
            <id>atom-1-id</id>
            <author>
                <name>Jane Smith</name>
                <email>jane@example.com</email>
            </author>
            <category term="science"/>
        </entry>
        
        <entry>
            <title>Atom Article 2</title>
            <summary>Summary of the second atom article</summary>
            <link href="https://example.com/atom-2"/>
            <updated>2024-01-15T09:45:00Z</updated>
            <id>atom-2-id</id>
        </entry>
    </feed>'''


class TestFeedFetcher:
    '''Test FeedFetcher service functionality'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [Category, Feed, Article]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    
    @pytest.fixture
    def sample_feed(self):
        '''Create a sample feed for testing'''
        category = Category.create(name='Technology')
        return Feed.create(
            url='https://example.com/feed.xml',
            title='Test Feed',
            description='A test feed',
            category=category,
            fetch_interval=3600
        )
    


class TestFeedFetchResult:
    '''Test FeedFetchResult data class'''
    
    def test_successful_fetch_result(self):
        '''Test creating a successful fetch result'''
        result = FeedFetchResult(
            success=True,
            feed_url='https://example.com/feed.xml',
            final_url='https://example.com/feed.xml',
            content='<rss>content</rss>',
            last_modified='Mon, 15 Jan 2024 10:30:00 GMT',
            etag='"abc123"',
            status_code=200,
            fetch_time=1.5
        )
        
        assert result.success is True
        assert result.feed_url == 'https://example.com/feed.xml'
        assert result.final_url == 'https://example.com/feed.xml'
        assert result.content == '<rss>content</rss>'
        assert result.last_modified == 'Mon, 15 Jan 2024 10:30:00 GMT'
        assert result.etag == '"abc123"'
        assert result.status_code == 200
        assert result.fetch_time == 1.5
        assert result.error_message is None
    
    def test_failed_fetch_result(self):
        '''Test creating a failed fetch result'''
        result = FeedFetchResult(
            success=False,
            feed_url='https://example.com/feed.xml',
            error_message='HTTP 404: Not Found',
            status_code=404,
            fetch_time=0.5
        )
        
        assert result.success is False
        assert result.feed_url == 'https://example.com/feed.xml'
        assert result.error_message == 'HTTP 404: Not Found'
        assert result.status_code == 404
        assert result.fetch_time == 0.5
        assert result.content is None
        assert result.final_url is None


class TestFeedFetchingBasics:
    '''Test basic feed fetching functionality'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [Category, Feed, Article]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    @pytest.mark.asyncio
    async def test_fetch_feed_success(self, feed_fetcher, sample_rss_content):
        '''Test successful feed fetching'''
        with aioresponses() as mock:
            mock.get(
                'https://example.com/feed.xml',
                payload=sample_rss_content,
                status=200,
                headers={
                    'Content-Type': 'application/rss+xml',
                    'Last-Modified': 'Mon, 15 Jan 2024 10:30:00 GMT',
                    'ETag': '"abc123"'
                }
            )
            
            result = await feed_fetcher.fetch_feed('https://example.com/feed.xml')
            
            assert result.success is True
            assert result.feed_url == 'https://example.com/feed.xml'
            assert result.final_url == 'https://example.com/feed.xml'
            assert sample_rss_content in result.content
            assert result.last_modified == 'Mon, 15 Jan 2024 10:30:00 GMT'
            assert result.etag == '"abc123"'
            assert result.status_code == 200
            assert result.fetch_time > 0
    
    def test_fetch_feed_http_error(self, feed_fetcher):
        '''Test feed fetching with HTTP error'''
        
        @pytest.mark.asyncio
        async def run_test():
            with aioresponses() as mock:
                mock.get(
                    'https://example.com/not-found.xml',
                    status=404
                )
                
                result = await feed_fetcher.fetch_feed('https://example.com/not-found.xml')
                
                assert result.success is False
                assert result.feed_url == 'https://example.com/not-found.xml'
                assert result.status_code == 404
                assert 'HTTP 404' in result.error_message
                assert result.content is None
        
        import asyncio
        asyncio.run(run_test())
    
    def test_fetch_feed_timeout(self, feed_fetcher):
        '''Test feed fetching with timeout'''
        
        @pytest.mark.asyncio
        async def run_test():
            with aioresponses() as mock:
                mock.get(
                    'https://example.com/slow-feed.xml',
                    exception=asyncio.TimeoutError()
                )
                
                result = await feed_fetcher.fetch_feed('https://example.com/slow-feed.xml')
                
                assert result.success is False
                assert result.feed_url == 'https://example.com/slow-feed.xml'
                assert 'timeout' in result.error_message.lower()
                assert result.content is None
        
        import asyncio
        asyncio.run(run_test())
    
    def test_fetch_feed_with_redirects(self, feed_fetcher, sample_rss_content):
        '''Test feed fetching with redirects'''
        
        @pytest.mark.asyncio
        async def run_test():
            with aioresponses() as mock:
                # First request redirects
                mock.get(
                    'https://example.com/old-feed.xml',
                    status=301,
                    headers={'Location': 'https://example.com/new-feed.xml'}
                )
                # Second request succeeds
                mock.get(
                    'https://example.com/new-feed.xml',
                    payload=sample_rss_content,
                    status=200
                )
                
                result = await feed_fetcher.fetch_feed('https://example.com/old-feed.xml')
                
                assert result.success is True
                assert result.feed_url == 'https://example.com/old-feed.xml'
                assert result.final_url == 'https://example.com/new-feed.xml'
                assert sample_rss_content in result.content
        
        import asyncio
        asyncio.run(run_test())
    
    def test_fetch_feed_with_conditional_requests(self, feed_fetcher):
        '''Test feed fetching with conditional requests (304 Not Modified)'''
        
        @pytest.mark.asyncio
        async def run_test():
            with aioresponses() as mock:
                mock.get(
                    'https://example.com/feed.xml',
                    status=304
                )
                
                result = await feed_fetcher.fetch_feed(
                    'https://example.com/feed.xml',
                    last_modified='Mon, 15 Jan 2024 10:30:00 GMT',
                    etag='"abc123"'
                )
                
                assert result.success is True
                assert result.feed_url == 'https://example.com/feed.xml'
                assert result.status_code == 304
                assert result.content is None  # No content for 304
        
        import asyncio
        asyncio.run(run_test())


class TestFeedParsing:
    '''Test feed parsing functionality'''
    
    def test_parse_rss_feed(self, feed_fetcher, sample_rss_content):
        '''Test parsing RSS feed content'''
        
        @pytest.mark.asyncio
        async def run_test():
            parsed = await feed_fetcher.parse_feed_content(sample_rss_content)
            
            assert parsed is not None
            assert parsed.feed.title == 'Test RSS Feed'
            assert parsed.feed.description == 'A test RSS feed'
            assert parsed.feed.link == 'https://example.com'
            
            # Check entries
            entries = parsed.entries
            assert len(entries) == 2
            
            # First entry
            first_entry = entries[0]
            assert first_entry.title == 'First Article'
            assert first_entry.description == 'Content of the first article'
            assert first_entry.link == 'https://example.com/article-1'
            assert first_entry.id == 'article-1-guid'
            assert 'Technology' in [tag.term for tag in first_entry.tags]
            
            # Second entry
            second_entry = entries[1]
            assert second_entry.title == 'Second Article'
            assert second_entry.link == 'https://example.com/article-2'
        
        import asyncio
        asyncio.run(run_test())
    
    def test_parse_atom_feed(self, feed_fetcher, sample_atom_content):
        '''Test parsing Atom feed content'''
        
        @pytest.mark.asyncio
        async def run_test():
            parsed = await feed_fetcher.parse_feed_content(sample_atom_content)
            
            assert parsed is not None
            assert parsed.feed.title == 'Test Atom Feed'
            assert parsed.feed.subtitle == 'A test Atom feed'
            assert parsed.feed.link == 'https://example.com'
            
            # Check entries
            entries = parsed.entries
            assert len(entries) == 2
            
            # First entry
            first_entry = entries[0]
            assert first_entry.title == 'Atom Article 1'
            assert 'HTML content' in first_entry.content[0].value
            assert first_entry.link == 'https://example.com/atom-1'
            assert first_entry.author == 'Jane Smith'
        
        import asyncio
        asyncio.run(run_test())
    
    def test_parse_invalid_feed_content(self, feed_fetcher):
        '''Test parsing invalid feed content'''
        
        @pytest.mark.asyncio
        async def run_test():
            invalid_content = '<html><body>This is not a feed</body></html>'
            
            with pytest.raises(FeedParseError):
                await feed_fetcher.parse_feed_content(invalid_content)
        
        import asyncio
        asyncio.run(run_test())
    
    def test_parse_empty_feed_content(self, feed_fetcher):
        '''Test parsing empty feed content'''
        
        @pytest.mark.asyncio
        async def run_test():
            with pytest.raises(FeedParseError):
                await feed_fetcher.parse_feed_content('')
        
        import asyncio
        asyncio.run(run_test())


class TestFeedUpdateTracking:
    '''Test feed update tracking functionality'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [Category, Feed, Article]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    @pytest.fixture
    def sample_feed(self):
        '''Create sample feed'''
        category = Category.create(name='Tech')
        return Feed.create(
            url='https://example.com/feed.xml',
            title='Tech Feed',
            category=category,
            fetch_interval=3600
        )
    
    def test_should_update_feed_never_fetched(self, feed_fetcher, sample_feed):
        '''Test that feed should be updated if never fetched'''
        # Feed has no last_fetched date
        assert sample_feed.last_fetched is None
        
        should_update = feed_fetcher.should_update_feed(sample_feed)
        assert should_update is True
    
    def test_should_update_feed_interval_elapsed(self, feed_fetcher, sample_feed):
        '''Test that feed should be updated if interval has elapsed'''
        # Set last_fetched to 2 hours ago (interval is 1 hour)
        sample_feed.last_fetched = datetime.now() - timedelta(hours=2)
        sample_feed.save()
        
        should_update = feed_fetcher.should_update_feed(sample_feed)
        assert should_update is True
    
    def test_should_not_update_feed_interval_not_elapsed(self, feed_fetcher, sample_feed):
        '''Test that feed should not be updated if interval has not elapsed'''
        # Set last_fetched to 30 minutes ago (interval is 1 hour)
        sample_feed.last_fetched = datetime.now() - timedelta(minutes=30)
        sample_feed.save()
        
        should_update = feed_fetcher.should_update_feed(sample_feed)
        assert should_update is False
    
    def test_should_update_feed_force_update(self, feed_fetcher, sample_feed):
        '''Test that feed can be force updated regardless of interval'''
        # Set last_fetched to 10 minutes ago
        sample_feed.last_fetched = datetime.now() - timedelta(minutes=10)
        sample_feed.save()
        
        # Should not update normally
        should_update = feed_fetcher.should_update_feed(sample_feed)
        assert should_update is False
        
        # Should update when forced
        should_update = feed_fetcher.should_update_feed(sample_feed, force=True)
        assert should_update is True
    
    def test_update_feed_last_fetched(self, feed_fetcher, sample_feed):
        '''Test updating feed last_fetched timestamp'''
        original_last_fetched = sample_feed.last_fetched
        
        feed_fetcher.update_feed_last_fetched(sample_feed)
        
        # Reload from database
        sample_feed = Feed.get_by_id(sample_feed.id)
        assert sample_feed.last_fetched != original_last_fetched
        assert sample_feed.last_fetched is not None
        
        # Should be recent
        time_diff = datetime.now() - sample_feed.last_fetched
        assert time_diff.total_seconds() < 5  # Within 5 seconds


class TestFeedFetcherConfiguration:
    '''Test FeedFetcher configuration options'''
    
    def test_custom_timeout(self):
        '''Test creating fetcher with custom timeout'''
        fetcher = FeedFetcher(timeout=60)
        assert fetcher.timeout == 60
    
    def test_custom_max_retries(self):
        '''Test creating fetcher with custom max retries'''
        fetcher = FeedFetcher(max_retries=5)
        assert fetcher.max_retries == 5
    
    def test_custom_user_agent(self):
        '''Test creating fetcher with custom user agent'''
        custom_ua = 'Custom RSS Reader/2.0'
        fetcher = FeedFetcher(user_agent=custom_ua)
        assert fetcher.user_agent == custom_ua
    
    def test_default_configuration(self):
        '''Test default fetcher configuration'''
        fetcher = FeedFetcher()
        assert fetcher.timeout == 30  # Default
        assert fetcher.max_retries == 3  # Default
        assert 'Zib RSS Reader' in fetcher.user_agent  # Default contains app name


class TestArticleExtraction:
    '''Test article extraction from parsed feeds'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [Category, Feed, Article]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    @pytest.fixture
    def sample_feed(self):
        '''Create sample feed'''
        category = Category.create(name='Tech')
        return Feed.create(
            url='https://example.com/feed.xml',
            title='Tech Feed',
            category=category
        )
    
    @pytest.fixture
    def parsed_rss_data(self):
        '''Mock parsed RSS data structure'''
        import types
        
        # Create mock parsed feed structure
        parsed = types.SimpleNamespace()
        parsed.feed = types.SimpleNamespace()
        parsed.feed.title = 'Test Feed'
        parsed.feed.description = 'A test feed'
        parsed.feed.link = 'https://example.com'
        
        # Create mock entries
        entry1 = types.SimpleNamespace()
        entry1.title = 'First Article'
        entry1.link = 'https://example.com/article-1'
        entry1.summary = 'Summary of first article'
        entry1.description = 'Content of first article'
        entry1.id = 'article-1-guid'
        entry1.author = 'John Doe'
        entry1.published_parsed = (2024, 1, 15, 10, 0, 0, 0, 15, -1)
        
        # Add tags
        tag1 = types.SimpleNamespace()
        tag1.term = 'technology'
        tag2 = types.SimpleNamespace()
        tag2.term = 'programming'
        entry1.tags = [tag1, tag2]
        
        entry2 = types.SimpleNamespace()
        entry2.title = 'Second Article'
        entry2.link = 'https://example.com/article-2'
        entry2.summary = 'Summary of second article'
        entry2.id = 'article-2-guid'
        # No author, tags, or published date
        
        parsed.entries = [entry1, entry2]
        return parsed
    
    def test_extract_articles_from_parsed_feed(self, feed_fetcher, sample_feed, parsed_rss_data):
        '''Test extracting articles from parsed feed data'''
        
        @pytest.mark.asyncio
        async def run_test():
            articles = await feed_fetcher.extract_articles_from_parsed_feed(
                sample_feed, parsed_rss_data
            )
            
            assert len(articles) == 2
            
            # Check first article
            article1 = articles[0]
            assert article1['title'] == 'First Article'
            assert article1['link'] == 'https://example.com/article-1'
            assert article1['summary'] == 'Summary of first article'
            assert article1['content'] == 'Content of first article'
            assert article1['id'] == 'article-1-guid'
            assert article1['author'] == 'John Doe'
            assert article1['tags'] == ['technology', 'programming']
            assert article1['published_parsed'] is not None
            
            # Check second article
            article2 = articles[1]
            assert article2['title'] == 'Second Article'
            assert article2['link'] == 'https://example.com/article-2'
            assert article2['id'] == 'article-2-guid'
            assert article2['author'] is None
            assert article2['tags'] == []
            assert article2['published_parsed'] is None
        
        import asyncio
        asyncio.run(run_test())
    
    def test_extract_author_from_entry(self, feed_fetcher):
        '''Test author extraction from different entry formats'''
        import types
        
        # Test direct author field
        entry1 = types.SimpleNamespace()
        entry1.author = 'John Doe'
        assert feed_fetcher._extract_author(entry1) == 'John Doe'
        
        # Test author_detail with name
        entry2 = types.SimpleNamespace()
        entry2.author_detail = types.SimpleNamespace()
        entry2.author_detail.name = 'Jane Smith'
        assert feed_fetcher._extract_author(entry2) == 'Jane Smith'
        
        # Test author_detail with email
        entry3 = types.SimpleNamespace()
        entry3.author_detail = types.SimpleNamespace()
        entry3.author_detail.email = 'author@example.com'
        assert feed_fetcher._extract_author(entry3) == 'author@example.com'
        
        # Test no author
        entry4 = types.SimpleNamespace()
        assert feed_fetcher._extract_author(entry4) is None
    
    def test_extract_tags_from_entry(self, feed_fetcher):
        '''Test tag extraction from different entry formats'''
        import types
        
        # Test structured tags
        entry1 = types.SimpleNamespace()
        tag1 = types.SimpleNamespace()
        tag1.term = 'python'
        tag2 = types.SimpleNamespace()
        tag2.term = 'programming'
        entry1.tags = [tag1, tag2]
        
        tags = feed_fetcher._extract_tags(entry1)
        assert tags == ['python', 'programming']
        
        # Test string tags
        entry2 = types.SimpleNamespace()
        entry2.tags = ['science', 'research']
        
        tags = feed_fetcher._extract_tags(entry2)
        assert tags == ['science', 'research']
        
        # Test no tags
        entry3 = types.SimpleNamespace()
        tags = feed_fetcher._extract_tags(entry3)
        assert tags == []
    
    def test_extract_content_from_entry(self, feed_fetcher):
        '''Test content extraction from different entry formats'''
        import types
        
        # Test Atom content field
        entry1 = types.SimpleNamespace()
        content1 = types.SimpleNamespace()
        content1.value = 'HTML content here'
        entry1.content = [content1]
        
        content = feed_fetcher._extract_content(entry1)
        assert content == 'HTML content here'
        
        # Test RSS description field
        entry2 = types.SimpleNamespace()
        entry2.description = 'RSS description content'
        
        content = feed_fetcher._extract_content(entry2)
        assert content == 'RSS description content'
        
        # Test summary field
        entry3 = types.SimpleNamespace()
        entry3.summary = 'Summary content'
        
        content = feed_fetcher._extract_content(entry3)
        assert content == 'Summary content'
        
        # Test no content
        entry4 = types.SimpleNamespace()
        content = feed_fetcher._extract_content(entry4)
        assert content is None


class TestFeedUpdateComplete:
    '''Test complete feed update workflow'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [Category, Feed, Article]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    @pytest.fixture
    def sample_feed(self):
        '''Create sample feed'''
        category = Category.create(name='Tech')
        return Feed.create(
            url='https://example.com/feed.xml',
            title='Tech Feed',
            category=category,
            fetch_interval=3600
        )
    
    def test_update_feed_complete_workflow(self, feed_fetcher, sample_feed, sample_rss_content):
        '''Test complete feed update workflow'''
        
        @pytest.mark.asyncio
        async def run_test():
            with aioresponses() as mock:
                mock.get(
                    'https://example.com/feed.xml',
                    payload=sample_rss_content,
                    status=200,
                    headers={'Content-Type': 'application/rss+xml'}
                )
                
                # Verify no articles initially
                assert Article.select().count() == 0
                
                # Update feed
                result = await feed_fetcher.update_feed(sample_feed)
                
                # Check result
                assert result.success is True
                assert result.feed == sample_feed
                assert result.articles_added == 2  # Two articles in sample RSS
                assert result.articles_updated == 0
                assert result.articles_failed == 0
                assert result.fetch_result is not None
                assert result.fetch_result.success is True
                
                # Verify articles were created
                articles = list(Article.select())
                assert len(articles) == 2
                
                # Check first article
                article1 = Article.get(Article.title == 'First Article')
                assert article1.feed == sample_feed
                assert article1.url == 'https://example.com/article-1'
                assert article1.guid == 'article-1-guid'
                assert article1.author == 'john@example.com (John Doe)'
                
                # Check feed was updated
                updated_feed = Feed.get_by_id(sample_feed.id)
                assert updated_feed.last_fetched is not None
                assert updated_feed.title == 'Test RSS Feed'  # Updated from feed
                assert updated_feed.description == 'A test RSS feed'  # Updated from feed
        
        import asyncio
        asyncio.run(run_test())
    
    def test_update_feed_with_duplicates(self, feed_fetcher, sample_feed, sample_rss_content):
        '''Test feed update with duplicate articles'''
        
        @pytest.mark.asyncio
        async def run_test():
            # Create an existing article first
            existing_article = Article.create(
                feed=sample_feed,
                title='Existing Article',
                url='https://example.com/article-1',  # Same URL as in RSS
                guid='existing-guid'
            )
            
            with aioresponses() as mock:
                mock.get(
                    'https://example.com/feed.xml',
                    payload=sample_rss_content,
                    status=200
                )
                
                # Update feed
                result = await feed_fetcher.update_feed(sample_feed)
                
                # Check result
                assert result.success is True
                assert result.articles_added == 1  # Only one new article
                assert result.articles_updated == 1  # One duplicate found
                assert result.articles_failed == 0
                
                # Verify total articles
                assert Article.select().count() == 2  # One existing + one new
        
        import asyncio
        asyncio.run(run_test())
    
    def test_update_feed_not_modified(self, feed_fetcher, sample_feed):
        '''Test feed update with 304 Not Modified response'''
        
        @pytest.mark.asyncio
        async def run_test():
            with aioresponses() as mock:
                mock.get(
                    'https://example.com/feed.xml',
                    status=304
                )
                
                result = await feed_fetcher.update_feed(sample_feed, force=True)
                
                assert result.success is True
                assert result.articles_added == 0
                assert result.articles_updated == 0
                assert result.fetch_result.status_code == 304
        
        import asyncio
        asyncio.run(run_test())
    
    def test_update_multiple_feeds(self, feed_fetcher, sample_rss_content):
        '''Test updating multiple feeds concurrently'''
        
        @pytest.mark.asyncio
        async def run_test():
            # Create multiple feeds
            category = Category.create(name='Tech')
            feeds = []
            for i in range(3):
                feed = Feed.create(
                    url=f'https://example.com/feed-{i}.xml',
                    title=f'Feed {i}',
                    category=category
                )
                feeds.append(feed)
            
            with aioresponses() as mock:
                # Mock responses for all feeds
                for i in range(3):
                    mock.get(
                        f'https://example.com/feed-{i}.xml',
                        payload=sample_rss_content,
                        status=200
                    )
                
                # Update all feeds
                results = await feed_fetcher.update_multiple_feeds(feeds, force=True)
                
                # Check results
                assert len(results) == 3
                for result in results:
                    assert result.success is True
                    assert result.articles_added == 2
                
                # Verify total articles created
                assert Article.select().count() == 6  # 3 feeds * 2 articles each
        
        import asyncio
        asyncio.run(run_test())