import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from peewee import IntegrityError
from app.models.article import Article, UserSubscription, ReadStatus
from app.models.base import Category, Feed
from app.core.database import db


class TestArticleModel:
    '''Test Article model functionality'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database with required tables'''
        # Create tables for testing
        models = [Category, Feed, Article, UserSubscription, ReadStatus]
        db.create_tables(models, safe=True)
        
        yield
        
        # Clean up after each test
        db.drop_tables(models, safe=True)
    
    @pytest.fixture
    def sample_category(self):
        '''Create a sample category for testing'''
        return Category.create(
            name='Technology',
            description='Tech news and articles'
        )
    
    @pytest.fixture
    def sample_feed(self, sample_category):
        '''Create a sample feed for testing'''
        return Feed.create(
            url='https://example.com/feed.xml',
            title='Example Tech Blog',
            description='A great tech blog',
            category=sample_category,
            fetch_interval=3600
        )
    
    @pytest.fixture
    def sample_article_data(self):
        '''Sample article data for testing'''
        return {
            'title': 'Test Article Title',
            'content': '<p>This is a test article with <strong>HTML</strong> content.</p>',
            'url': 'https://example.com/article-1',
            'guid': 'article-1-guid',
            'published_date': datetime(2024, 1, 15, 10, 30, 0),
            'author': 'John Doe',
            'summary': 'A brief summary of the test article.',
            'tags': 'technology,programming,web'
        }
    
    def test_create_article_with_required_fields(self, sample_feed, sample_article_data):
        '''Test creating an article with all required fields'''
        article = Article.create(
            feed=sample_feed,
            **sample_article_data
        )
        
        assert article.id is not None
        assert article.feed == sample_feed
        assert article.title == sample_article_data['title']
        assert article.content == sample_article_data['content']
        assert article.url == sample_article_data['url']
        assert article.guid == sample_article_data['guid']
        assert article.published_date == sample_article_data['published_date']
        assert article.author == sample_article_data['author']
        assert article.summary == sample_article_data['summary']
        assert article.tags == sample_article_data['tags']
        assert article.created_at is not None
        assert article.updated_at is not None
    
    def test_create_article_with_minimal_fields(self, sample_feed):
        '''Test creating an article with only required fields'''
        article = Article.create(
            feed=sample_feed,
            title='Minimal Article',
            url='https://example.com/minimal',
            guid='minimal-guid'
        )
        
        assert article.id is not None
        assert article.feed == sample_feed
        assert article.title == 'Minimal Article'
        assert article.url == 'https://example.com/minimal'
        assert article.guid == 'minimal-guid'
        assert article.content is None
        assert article.published_date is None
        assert article.author is None
        assert article.summary is None
        assert article.tags is None
    
    def test_article_url_must_be_unique_per_feed(self, sample_feed):
        '''Test that article URLs must be unique within the same feed'''
        # Create first article
        Article.create(
            feed=sample_feed,
            title='First Article',
            url='https://example.com/same-url',
            guid='first-guid'
        )
        
        # Try to create second article with same URL in same feed
        with pytest.raises(IntegrityError):
            Article.create(
                feed=sample_feed,
                title='Second Article',
                url='https://example.com/same-url',
                guid='second-guid'
            )
    
    def test_article_guid_must_be_unique_per_feed(self, sample_feed):
        '''Test that article GUIDs must be unique within the same feed'''
        # Create first article
        Article.create(
            feed=sample_feed,
            title='First Article',
            url='https://example.com/first',
            guid='same-guid'
        )
        
        # Try to create second article with same GUID in same feed
        with pytest.raises(IntegrityError):
            Article.create(
                feed=sample_feed,
                title='Second Article',
                url='https://example.com/second',
                guid='same-guid'
            )
    
    def test_article_feed_relationship(self, sample_feed, sample_article_data):
        '''Test the relationship between article and feed'''
        article = Article.create(
            feed=sample_feed,
            **sample_article_data
        )
        
        # Test forward relationship
        assert article.feed == sample_feed
        assert article.feed.title == 'Example Tech Blog'
        
        # Test reverse relationship (backref)
        feed_articles = list(sample_feed.articles)
        assert len(feed_articles) == 1
        assert feed_articles[0] == article
    
    def test_article_category_access_through_feed(self, sample_feed, sample_article_data):
        '''Test accessing category through feed relationship'''
        article = Article.create(
            feed=sample_feed,
            **sample_article_data
        )
        
        assert article.feed.category.name == 'Technology'
        assert article.feed.category.description == 'Tech news and articles'
    
    def test_article_content_sanitization_validation(self, sample_feed):
        '''Test article content sanitization (placeholder for future implementation)'''
        # This test validates that we can store HTML content
        # Sanitization logic will be implemented in the model
        malicious_content = '<script>alert("xss")</script><p>Safe content</p>'
        
        article = Article.create(
            feed=sample_feed,
            title='Test Sanitization',
            url='https://example.com/sanitize',
            guid='sanitize-guid',
            content=malicious_content
        )
        
        # For now, content is stored as-is
        # TODO: Implement content sanitization
        assert article.content == malicious_content
    
    def test_article_tags_handling(self, sample_feed):
        '''Test article tags storage and retrieval'''
        article = Article.create(
            feed=sample_feed,
            title='Tagged Article',
            url='https://example.com/tagged',
            guid='tagged-guid',
            tags='python,web-development,tutorial,beginner'
        )
        
        assert article.tags == 'python,web-development,tutorial,beginner'
        
        # Test tag parsing method
        tag_list = article.get_tag_list()
        expected_tags = ['python', 'web-development', 'tutorial', 'beginner']
        assert tag_list == expected_tags
    
    def test_article_timestamps(self, sample_feed):
        '''Test article timestamp handling'''
        before_creation = datetime.now()
        
        article = Article.create(
            feed=sample_feed,
            title='Timestamp Test',
            url='https://example.com/timestamp',
            guid='timestamp-guid',
            published_date=datetime(2024, 1, 10, 14, 30, 0)
        )
        
        after_creation = datetime.now()
        
        # Test created_at timestamp
        assert before_creation <= article.created_at <= after_creation
        assert before_creation <= article.updated_at <= after_creation
        
        # Test published_date
        assert article.published_date == datetime(2024, 1, 10, 14, 30, 0)
    
    def test_article_save_updates_timestamp(self, sample_feed, sample_article_data):
        '''Test that saving an article updates the updated_at timestamp'''
        article = Article.create(
            feed=sample_feed,
            **sample_article_data
        )
        
        original_updated_at = article.updated_at
        
        # Wait a moment and update
        import time
        time.sleep(0.01)
        
        article.title = 'Updated Title'
        article.save()
        
        assert article.updated_at > original_updated_at
    
    def test_article_string_representation(self, sample_feed, sample_article_data):
        '''Test article string representation'''
        article = Article.create(
            feed=sample_feed,
            **sample_article_data
        )
        
        assert str(article) == 'Test Article Title'
        
        # Test with article without title
        article_no_title = Article.create(
            feed=sample_feed,
            title=None,
            url='https://example.com/no-title',
            guid='no-title-guid'
        )
        
        assert str(article_no_title) == 'https://example.com/no-title'
    
    def test_article_word_count_calculation(self, sample_feed):
        '''Test word count calculation for articles'''
        content = '''
        <p>This is a test article with multiple paragraphs.</p>
        <p>It contains <strong>HTML tags</strong> and should calculate word count correctly.</p>
        <div>Total words should be counted properly.</div>
        '''
        
        article = Article.create(
            feed=sample_feed,
            title='Word Count Test',
            url='https://example.com/word-count',
            guid='word-count-guid',
            content=content
        )
        
        word_count = article.get_word_count()
        # Should strip HTML and count words
        assert word_count > 0
        assert isinstance(word_count, int)
    
    def test_article_reading_time_estimation(self, sample_feed):
        '''Test reading time estimation for articles'''
        # Create a longer article
        long_content = ' '.join(['This is a test word.'] * 250)  # ~1000 words
        
        article = Article.create(
            feed=sample_feed,
            title='Long Article',
            url='https://example.com/long',
            guid='long-guid',
            content=long_content
        )
        
        reading_time = article.get_estimated_reading_time()
        assert reading_time > 0
        assert isinstance(reading_time, int)
        # Should be roughly 4-5 minutes for 1000 words
        assert 3 <= reading_time <= 6


class TestArticleDeduplication:
    '''Test article deduplication logic'''
    
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
        category = Category.create(name='Test Category')
        return Feed.create(
            url='https://example.com/feed.xml',
            title='Test Feed',
            category=category
        )
    
    def test_find_duplicate_by_url(self, sample_feed):
        '''Test finding duplicate articles by URL'''
        # Create original article
        original = Article.create(
            feed=sample_feed,
            title='Original Article',
            url='https://example.com/article',
            guid='original-guid'
        )
        
        # Check for duplicate by URL
        duplicate = Article.find_duplicate(
            feed=sample_feed,
            url='https://example.com/article',
            guid='different-guid'
        )
        
        assert duplicate == original
    
    def test_find_duplicate_by_guid(self, sample_feed):
        '''Test finding duplicate articles by GUID'''
        # Create original article
        original = Article.create(
            feed=sample_feed,
            title='Original Article',
            url='https://example.com/original',
            guid='same-guid'
        )
        
        # Check for duplicate by GUID
        duplicate = Article.find_duplicate(
            feed=sample_feed,
            url='https://example.com/different',
            guid='same-guid'
        )
        
        assert duplicate == original
    
    def test_no_duplicate_found(self, sample_feed):
        '''Test when no duplicate exists'''
        # Create original article
        Article.create(
            feed=sample_feed,
            title='Original Article',
            url='https://example.com/original',
            guid='original-guid'
        )
        
        # Check for non-existent duplicate
        duplicate = Article.find_duplicate(
            feed=sample_feed,
            url='https://example.com/different',
            guid='different-guid'
        )
        
        assert duplicate is None
    
    def test_duplicate_detection_scope_per_feed(self, sample_feed):
        '''Test that duplicate detection is scoped per feed'''
        # Create second feed
        category = Category.create(name='Other Category')
        other_feed = Feed.create(
            url='https://other.com/feed.xml',
            title='Other Feed',
            category=category
        )
        
        # Create article in first feed
        Article.create(
            feed=sample_feed,
            title='Article',
            url='https://example.com/article',
            guid='same-guid'
        )
        
        # Same URL/GUID in different feed should not be considered duplicate
        duplicate = Article.find_duplicate(
            feed=other_feed,
            url='https://example.com/article',
            guid='same-guid'
        )
        
        assert duplicate is None


class TestArticleCreationFromFeedEntry:
    '''Test creating articles from parsed feed entries'''
    
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
        category = Category.create(name='Test Category')
        return Feed.create(
            url='https://example.com/feed.xml',
            title='Test Feed',
            category=category
        )
    
    @pytest.fixture
    def sample_feed_entry(self):
        '''Sample parsed feed entry data'''
        return {
            'title': 'Sample Article Title',
            'content': '<p>Article content with <strong>formatting</strong></p>',
            'summary': 'Article summary text',
            'link': 'https://example.com/article-1',
            'id': 'article-1-guid',
            'author': 'Jane Doe',
            'tags': ['python', 'programming', 'tutorial'],
            'published_parsed': (2024, 1, 15, 14, 30, 0, 0, 15, -1)  # time.struct_time format
        }
    
    def test_create_article_from_complete_feed_entry(self, sample_feed, sample_feed_entry):
        '''Test creating article from complete feed entry'''
        article = Article.create_from_feed_entry(sample_feed, sample_feed_entry)
        
        assert article.feed == sample_feed
        assert article.title == 'Sample Article Title'
        assert article.content == '<p>Article content with <strong>formatting</strong></p>'
        assert article.summary == 'Article summary text'
        assert article.url == 'https://example.com/article-1'
        assert article.guid == 'article-1-guid'
        assert article.author == 'Jane Doe'
        assert article.tags == 'python,programming,tutorial'
        assert article.published_date.year == 2024
        assert article.published_date.month == 1
        assert article.published_date.day == 15
    
    def test_create_article_from_minimal_feed_entry(self, sample_feed):
        '''Test creating article from minimal feed entry'''
        minimal_entry = {
            'title': 'Minimal Article',
            'link': 'https://example.com/minimal'
        }
        
        article = Article.create_from_feed_entry(sample_feed, minimal_entry)
        
        assert article.feed == sample_feed
        assert article.title == 'Minimal Article'
        assert article.url == 'https://example.com/minimal'
        assert article.guid == 'https://example.com/minimal'  # Falls back to link
        assert article.content is None
        assert article.summary is None
        assert article.author is None
        assert article.tags is None
        assert article.published_date is None
    
    def test_create_article_with_description_fallback(self, sample_feed):
        '''Test that description is used when content is not available'''
        entry_with_description = {
            'title': 'Article with Description',
            'description': 'This is the description content',
            'link': 'https://example.com/desc-article',
            'id': 'desc-guid'
        }
        
        article = Article.create_from_feed_entry(sample_feed, entry_with_description)
        
        assert article.content == 'This is the description content'
    
    def test_create_article_with_guid_fallback(self, sample_feed):
        '''Test GUID fallback logic'''
        # Test with explicit ID
        entry_with_id = {
            'title': 'Article with ID',
            'link': 'https://example.com/with-id',
            'id': 'explicit-id'
        }
        
        article1 = Article.create_from_feed_entry(sample_feed, entry_with_id)
        assert article1.guid == 'explicit-id'
        
        # Test with GUID field
        entry_with_guid = {
            'title': 'Article with GUID',
            'link': 'https://example.com/with-guid',
            'guid': 'explicit-guid'
        }
        
        article2 = Article.create_from_feed_entry(sample_feed, entry_with_guid)
        assert article2.guid == 'explicit-guid'
        
        # Test fallback to link
        entry_no_guid = {
            'title': 'Article without GUID',
            'link': 'https://example.com/no-guid'
        }
        
        article3 = Article.create_from_feed_entry(sample_feed, entry_no_guid)
        assert article3.guid == 'https://example.com/no-guid'
    
    def test_create_article_with_invalid_published_date(self, sample_feed):
        '''Test handling of invalid published date'''
        entry_bad_date = {
            'title': 'Article with Bad Date',
            'link': 'https://example.com/bad-date',
            'id': 'bad-date-guid',
            'published_parsed': 'invalid-date-format'
        }
        
        article = Article.create_from_feed_entry(sample_feed, entry_bad_date)
        
        # Should handle gracefully and leave published_date as None
        assert article.published_date is None
    
    def test_create_article_handles_empty_tags(self, sample_feed):
        '''Test handling of empty tags list'''
        entry_empty_tags = {
            'title': 'Article with Empty Tags',
            'link': 'https://example.com/empty-tags',
            'id': 'empty-tags-guid',
            'tags': []
        }
        
        article = Article.create_from_feed_entry(sample_feed, entry_empty_tags)
        assert article.tags is None
    
    def test_create_article_with_additional_kwargs(self, sample_feed):
        '''Test creating article with additional keyword arguments'''
        entry = {
            'title': 'Basic Article',
            'link': 'https://example.com/basic',
            'id': 'basic-guid'
        }
        
        # Add custom data via kwargs
        article = Article.create_from_feed_entry(
            sample_feed, 
            entry,
            custom_field='custom_value'  # This would be ignored by the model
        )
        
        assert article.title == 'Basic Article'
        assert article.url == 'https://example.com/basic'


class TestArticleContentProcessing:
    '''Test article content processing methods'''
    
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
        category = Category.create(name='Test Category')
        return Feed.create(
            url='https://example.com/feed.xml',
            title='Test Feed',
            category=category
        )
    
    def test_get_tag_list_parsing(self, sample_feed):
        '''Test tag list parsing'''
        article = Article.create(
            feed=sample_feed,
            title='Tagged Article',
            url='https://example.com/tagged',
            guid='tagged-guid',
            tags='python, web development,machine-learning,  data science  '
        )
        
        tag_list = article.get_tag_list()
        expected = ['python', 'web development', 'machine-learning', 'data science']
        assert tag_list == expected
    
    def test_get_tag_list_empty(self, sample_feed):
        '''Test tag list parsing with empty tags'''
        article = Article.create(
            feed=sample_feed,
            title='No Tags Article',
            url='https://example.com/no-tags',
            guid='no-tags-guid',
            tags=None
        )
        
        assert article.get_tag_list() == []
        
        # Test with empty string
        article.tags = ''
        assert article.get_tag_list() == []
        
        # Test with only commas and spaces
        article.tags = ' , , , '
        assert article.get_tag_list() == []
    
    def test_set_tag_list(self, sample_feed):
        '''Test setting tags from list'''
        article = Article.create(
            feed=sample_feed,
            title='Set Tags Article',
            url='https://example.com/set-tags',
            guid='set-tags-guid'
        )
        
        # Set tags from list
        tag_list = ['python', 'tutorial', 'beginner']
        article.set_tag_list(tag_list)
        
        assert article.tags == 'python,tutorial,beginner'
        assert article.get_tag_list() == tag_list
        
        # Test with empty list
        article.set_tag_list([])
        assert article.tags is None
        
        # Test with None
        article.set_tag_list(None)
        assert article.tags is None
    
    def test_word_count_with_html_content(self, sample_feed):
        '''Test word count calculation strips HTML'''
        html_content = '''
        <h1>Article Title</h1>
        <p>This is a <strong>test article</strong> with <em>various</em> HTML tags.</p>
        <div class="content">
            <p>It should count words correctly.</p>
            <ul>
                <li>Even in lists</li>
                <li>And other elements</li>
            </ul>
        </div>
        <script>console.log('this should be ignored');</script>
        '''
        
        article = Article.create(
            feed=sample_feed,
            title='HTML Content Article',
            url='https://example.com/html-content',
            guid='html-content-guid',
            content=html_content
        )
        
        word_count = article.get_word_count()
        # Should count words but ignore HTML tags and script content
        assert word_count > 10  # Should have counted the text words
        assert isinstance(word_count, int)
    
    def test_word_count_with_no_content(self, sample_feed):
        '''Test word count with no content'''
        article = Article.create(
            feed=sample_feed,
            title='No Content Article',
            url='https://example.com/no-content',
            guid='no-content-guid',
            content=None
        )
        
        assert article.get_word_count() == 0
        
        # Test with empty string
        article.content = ''
        assert article.get_word_count() == 0
    
    def test_estimated_reading_time(self, sample_feed):
        '''Test reading time estimation'''
        # Create content with known word count
        content = ' '.join(['word'] * 200)  # Exactly 200 words
        
        article = Article.create(
            feed=sample_feed,
            title='Reading Time Article',
            url='https://example.com/reading-time',
            guid='reading-time-guid',
            content=content
        )
        
        # Default WPM is 200, so 200 words = 1 minute
        reading_time = article.get_estimated_reading_time()
        assert reading_time == 1
        
        # Test with custom WPM
        reading_time_slow = article.get_estimated_reading_time(words_per_minute=100)
        assert reading_time_slow == 2
        
        # Test minimum of 1 minute
        short_article = Article.create(
            feed=sample_feed,
            title='Short Article',
            url='https://example.com/short',
            guid='short-guid',
            content='Just a few words here.'
        )
        
        assert short_article.get_estimated_reading_time() == 1