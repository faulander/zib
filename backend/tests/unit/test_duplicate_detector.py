import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.opml.duplicate_detector import (
    DuplicateDetector,
    DuplicateDetectionError,
    DuplicateResolution,
    FeedDuplicate,
    CategoryDuplicate
)
from app.models.base import Feed, Category


class TestDuplicateDetector:
    '''Test duplicate detection functionality'''
    
    @pytest.fixture
    def user_id(self):
        '''User ID for testing'''
        return 123
    
    @pytest.fixture
    def detector(self, user_id):
        '''Create a duplicate detector instance'''
        return DuplicateDetector(user_id)
    
    @pytest.fixture
    def sample_feeds(self):
        '''Sample feed data from OPML'''
        return [
            {
                'title': 'TechCrunch',
                'xml_url': 'https://techcrunch.com/feed/',
                'html_url': 'https://techcrunch.com/',
                'category_path': 'Technology'
            },
            {
                'title': 'Hacker News',
                'xml_url': 'https://news.ycombinator.com/rss',
                'html_url': 'https://news.ycombinator.com/',
                'category_path': 'Technology'
            },
            {
                'title': 'The Verge',
                'xml_url': 'https://www.theverge.com/rss/index.xml',
                'html_url': 'https://www.theverge.com/',
                'category_path': 'Technology'
            }
        ]
    
    @pytest.fixture
    def sample_categories(self):
        '''Sample category data from OPML'''
        return [
            {
                'name': 'Technology',
                'parent_path': None,
                'full_path': 'Technology',
                'description': 'Tech news and updates'
            },
            {
                'name': 'Startups',
                'parent_path': 'Technology',
                'full_path': 'Technology/Startups',
                'description': 'Startup news'
            },
            {
                'name': 'Science',
                'parent_path': None,
                'full_path': 'Science',
                'description': 'Scientific articles'
            }
        ]
    
    @pytest.fixture
    def existing_feeds(self, user_id):
        '''Mock existing feeds in database'''
        feeds = []
        
        # Create mock feed that matches one from sample
        feed1 = Mock(spec=Feed)
        feed1.id = 1
        feed1.user_id = user_id
        feed1.title = 'TechCrunch News'
        feed1.url = 'https://techcrunch.com/feed/'
        feed1.site_url = 'https://techcrunch.com/'
        feeds.append(feed1)
        
        # Create another existing feed
        feed2 = Mock(spec=Feed)
        feed2.id = 2
        feed2.user_id = user_id
        feed2.title = 'Existing Blog'
        feed2.url = 'https://example.com/feed.xml'
        feed2.site_url = 'https://example.com/'
        feeds.append(feed2)
        
        return feeds
    
    @pytest.fixture
    def existing_categories(self, user_id):
        '''Mock existing categories in database'''
        categories = []
        
        # Create mock category that matches one from sample
        cat1 = Mock(spec=Category)
        cat1.id = 1
        cat1.name = 'Technology'
        categories.append(cat1)
        
        # Create another category
        cat2 = Mock(spec=Category)
        cat2.id = 2
        cat2.name = 'News'
        categories.append(cat2)
        
        return categories
    
    def test_url_normalization(self, detector):
        '''Test feed URL normalization'''
        test_cases = [
            ('https://example.com/feed/', 'https://example.com/feed'),
            ('HTTP://EXAMPLE.COM/FEED', 'http://example.com/feed'),
            ('https://example.com//feed//rss', 'https://example.com/feed/rss'),
            ('https://example.com/feed?param=1', 'https://example.com/feed?param=1'),
            ('https://example.com/feed#section', 'https://example.com/feed'),
            ('  https://example.com/feed  ', 'https://example.com/feed'),
            ('', ''),
            ('example.com/feed', 'https://example.com/feed'),  # URL without scheme
        ]
        
        for input_url, expected in test_cases:
            result = detector._normalize_feed_url(input_url)
            assert result == expected, f'Failed for {input_url}: got {result}, expected {expected}'
    
    @pytest.mark.asyncio
    async def test_load_existing_data(self, detector, existing_feeds, existing_categories):
        '''Test loading existing feeds and categories'''
        with patch('app.services.opml.duplicate_detector.Feed.select') as mock_feed_select:
            with patch('app.services.opml.duplicate_detector.Category.select') as mock_cat_select:
                # Mock database queries - return the existing data directly
                mock_feed_select.return_value = existing_feeds
                mock_cat_select.return_value = existing_categories
                
                await detector.load_existing_data()
                
                # Verify feeds were loaded
                assert len(detector._existing_feeds) == 2
                assert 'https://techcrunch.com/feed' in detector._existing_feeds
                assert 'https://example.com/feed.xml' in detector._existing_feeds
                
                # Verify categories were loaded
                assert len(detector._existing_categories) == 2
                assert 'Technology' in detector._existing_categories
                assert 'News' in detector._existing_categories
    
    @pytest.mark.asyncio
    async def test_detect_feed_duplicates(self, detector, sample_feeds, existing_feeds):
        '''Test feed duplicate detection'''
        # Mock existing data
        detector._existing_feeds = {
            'https://techcrunch.com/feed': existing_feeds[0]
        }
        
        duplicates = detector.detect_feed_duplicates(sample_feeds)
        
        # Should find one duplicate (TechCrunch)
        assert len(duplicates) == 1
        assert duplicates[0].opml_feed['title'] == 'TechCrunch'
        assert duplicates[0].existing_feed == existing_feeds[0]
        assert duplicates[0].normalized_url == 'https://techcrunch.com/feed'
        assert duplicates[0].resolution.action == 'skip'
    
    @pytest.mark.asyncio
    async def test_detect_category_duplicates(self, detector, sample_categories, existing_categories):
        '''Test category duplicate detection'''
        # Mock existing data
        detector._existing_categories = {
            'Technology': existing_categories[0]
        }
        
        duplicates = detector.detect_category_duplicates(sample_categories)
        
        # Should find one duplicate (Technology)
        assert len(duplicates) == 1
        assert duplicates[0].opml_category['name'] == 'Technology'
        assert duplicates[0].existing_category == existing_categories[0]
        assert duplicates[0].path == 'Technology'
        assert duplicates[0].resolution.action == 'merge'
    
    def test_get_unique_feeds(self, detector, sample_feeds):
        '''Test getting unique feeds after duplicate resolution'''
        # Create mock duplicate that should be skipped
        duplicate = FeedDuplicate(
            opml_feed=sample_feeds[0],  # TechCrunch
            existing_feed=Mock(),
            normalized_url='https://techcrunch.com/feed',
            resolution=DuplicateResolution(action='skip')
        )
        
        unique_feeds = detector.get_unique_feeds(sample_feeds, [duplicate])
        
        # Should return 2 feeds (excluding the skipped duplicate)
        assert len(unique_feeds) == 2
        assert unique_feeds[0]['title'] == 'Hacker News'
        assert unique_feeds[1]['title'] == 'The Verge'
    
    def test_get_unique_categories(self, detector, sample_categories):
        '''Test getting unique categories after duplicate resolution'''
        # Create mock duplicate that should be merged
        duplicate = CategoryDuplicate(
            opml_category=sample_categories[0],  # Technology
            existing_category=Mock(),
            path='Technology',
            resolution=DuplicateResolution(action='merge')
        )
        
        unique_categories = detector.get_unique_categories(sample_categories, [duplicate])
        
        # Should return 2 categories (excluding the merged duplicate)
        assert len(unique_categories) == 2
        assert unique_categories[0]['name'] == 'Startups'
        assert unique_categories[1]['name'] == 'Science'
    
    def test_resolve_feed_duplicate_skip_existing(self, detector):
        '''Test feed duplicate resolution with skip_existing_feeds=True'''
        detector.skip_existing_feeds = True
        
        existing_feed = Mock(spec=Feed)
        existing_feed.id = 1
        existing_feed.title = 'Existing Feed'
        
        duplicate = FeedDuplicate(
            opml_feed={'title': 'New Feed'},
            existing_feed=existing_feed,
            normalized_url='https://example.com/feed'
        )
        
        resolution = detector._resolve_feed_duplicate(duplicate)
        
        assert resolution.action == 'skip'
        assert resolution.existing_id == 1
        assert 'already exists' in resolution.reason
    
    def test_resolve_feed_duplicate_replace(self, detector):
        '''Test feed duplicate resolution with skip_existing_feeds=False'''
        detector.skip_existing_feeds = False
        
        existing_feed = Mock(spec=Feed)
        existing_feed.id = 1
        existing_feed.title = 'Existing Feed'
        
        duplicate = FeedDuplicate(
            opml_feed={'title': 'New Feed'},
            existing_feed=existing_feed,
            normalized_url='https://example.com/feed'
        )
        
        resolution = detector._resolve_feed_duplicate(duplicate)
        
        assert resolution.action == 'replace'
        assert resolution.existing_id == 1
        assert 'Replacing existing feed' in resolution.reason
    
    def test_resolve_category_duplicate_merge(self, detector):
        '''Test category duplicate resolution with merge_categories=True'''
        detector.merge_categories = True
        
        existing_category = Mock(spec=Category)
        existing_category.id = 1
        existing_category.name = 'Technology'
        
        duplicate = CategoryDuplicate(
            opml_category={'name': 'Technology'},
            existing_category=existing_category,
            path='Technology'
        )
        
        resolution = detector._resolve_category_duplicate(duplicate)
        
        assert resolution.action == 'merge'
        assert resolution.existing_id == 1
        assert 'Merging with existing' in resolution.reason
    
    def test_resolve_category_duplicate_create_new(self, detector):
        '''Test category duplicate resolution with merge_categories=False'''
        detector.merge_categories = False
        
        # Mock the category name check
        with patch.object(detector, '_category_name_exists', return_value=False):
            existing_category = Mock(spec=Category)
            existing_category.id = 1
            existing_category.name = 'Technology'
            
            duplicate = CategoryDuplicate(
                opml_category={'name': 'Technology'},
                existing_category=existing_category,
                path='Technology'
            )
            
            resolution = detector._resolve_category_duplicate(duplicate)
            
            assert resolution.action == 'create_new'
            assert resolution.new_name == 'Technology (Imported 1)'
            assert 'Creating new category' in resolution.reason
    
    def test_category_name_collision_handling(self, detector):
        '''Test handling of category name collisions'''
        detector.merge_categories = False
        
        # Mock category name exists check - first collision, then available
        with patch.object(detector, '_category_name_exists', side_effect=[True, False]):
            existing_category = Mock(spec=Category)
            existing_category.id = 1
            existing_category.name = 'Technology'
            
            duplicate = CategoryDuplicate(
                opml_category={'name': 'Technology'},
                existing_category=existing_category,
                path='Technology'
            )
            
            resolution = detector._resolve_category_duplicate(duplicate)
            
            assert resolution.action == 'create_new'
            assert resolution.new_name == 'Technology (Imported 2)'
    
    def test_build_category_path(self, detector):
        '''Test building category paths'''
        # Mock category (simplified for current model)
        category = Mock(spec=Category)
        category.id = 1
        category.name = 'Technology'
        
        path = detector._build_category_path(category)
        assert path == 'Technology'
    
    def test_get_import_summary(self, detector, sample_feeds, sample_categories):
        '''Test generating import summary'''
        # Create mock duplicates
        feed_duplicate = FeedDuplicate(
            opml_feed=sample_feeds[0],
            existing_feed=Mock(title='Existing TechCrunch'),
            normalized_url='https://techcrunch.com/feed',
            resolution=DuplicateResolution(action='skip', reason='Already exists')
        )
        
        category_duplicate = CategoryDuplicate(
            opml_category=sample_categories[0],
            existing_category=Mock(name='Technology'),
            path='Technology',
            resolution=DuplicateResolution(action='merge', reason='Merging categories')
        )
        
        summary = detector.get_import_summary(
            sample_feeds, 
            sample_categories,
            [feed_duplicate],
            [category_duplicate]
        )
        
        assert summary['total_feeds'] == 3
        assert summary['total_categories'] == 3
        assert summary['new_feeds'] == 2  # 3 total - 1 duplicate
        assert summary['new_categories'] == 2  # 3 total - 1 duplicate
        assert summary['duplicate_feeds'] == 1
        assert summary['duplicate_categories'] == 1
        
        # Check duplicate details
        assert len(summary['feed_duplicates']) == 1
        assert summary['feed_duplicates'][0]['title'] == 'TechCrunch'
        assert summary['feed_duplicates'][0]['action'] == 'skip'
        
        assert len(summary['category_duplicates']) == 1
        assert summary['category_duplicates'][0]['name'] == 'Technology'
        assert summary['category_duplicates'][0]['action'] == 'merge'
    
    def test_detector_configuration(self, user_id):
        '''Test detector configuration options'''
        # Test default configuration
        detector1 = DuplicateDetector(user_id)
        assert detector1.merge_categories is True
        assert detector1.skip_existing_feeds is True
        
        # Test custom configuration
        detector2 = DuplicateDetector(user_id, merge_categories=False, skip_existing_feeds=False)
        assert detector2.merge_categories is False
        assert detector2.skip_existing_feeds is False
    
    @pytest.mark.asyncio
    async def test_load_existing_data_error_handling(self, detector):
        '''Test error handling during data loading'''
        with patch('app.services.opml.duplicate_detector.Feed.select', 
                   side_effect=Exception('Database error')):
            with pytest.raises(DuplicateDetectionError) as exc_info:
                await detector.load_existing_data()
            
            assert 'Failed to load existing data' in str(exc_info.value)
    
    def test_url_normalization_edge_cases(self, detector):
        '''Test URL normalization edge cases'''
        # Test None input
        assert detector._normalize_feed_url(None) == ''
        
        # Test empty string
        assert detector._normalize_feed_url('') == ''
        
        # Test URL with no scheme
        result = detector._normalize_feed_url('example.com/feed')
        assert result == 'https://example.com/feed'
        
        # Test malformed URL that causes exception
        with patch('app.services.opml.duplicate_detector.urlparse', 
                   side_effect=Exception('Parse error')):
            result = detector._normalize_feed_url('bad-url')
            assert result == 'bad-url'