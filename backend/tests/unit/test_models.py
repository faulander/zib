import pytest
import json
from datetime import datetime
from peewee import IntegrityError, SqliteDatabase
from app.core.database import BaseModel
from app.models.base import Category, Feed, Filter, SchemaVersion


# Test database for isolated testing
test_db = SqliteDatabase(':memory:', pragmas={'foreign_keys': 1})


class TestBaseModel:
    '''Test base model functionality'''
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        '''Setup test database for each test'''
        # Bind models to test database
        models = [Category, Feed, Filter, SchemaVersion]
        test_db.bind(models)
        test_db.connect()
        test_db.create_tables(models)
        
        yield
        
        # Cleanup
        test_db.drop_tables(models)
        test_db.close()
    
    def test_base_model_creation(self):
        '''Test that models inherit from BaseModel correctly'''
        category = Category(name='Test Category')
        assert isinstance(category, BaseModel)
        assert hasattr(category, 'created_at')
        assert hasattr(category, 'updated_at')


class TestCategory:
    '''Test Category model'''
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        '''Setup test database for each test'''
        models = [Category, Feed, Filter, SchemaVersion]
        test_db.bind(models)
        test_db.connect()
        test_db.create_tables(models)
        
        yield
        
        test_db.drop_tables(models)
        test_db.close()
    
    def test_category_creation(self):
        '''Test creating a category'''
        category = Category.create(
            name='Technology',
            description='Tech news and articles',
            color='#3B82F6'
        )
        
        assert category.id is not None
        assert category.name == 'Technology'
        assert category.description == 'Tech news and articles'
        assert category.color == '#3B82F6'
        assert isinstance(category.created_at, datetime)
        assert isinstance(category.updated_at, datetime)
    
    def test_category_name_unique(self):
        '''Test that category names must be unique'''
        Category.create(name='Technology')
        
        with pytest.raises(IntegrityError):
            Category.create(name='Technology')
    
    def test_category_required_fields(self):
        '''Test that name is required'''
        with pytest.raises(IntegrityError):
            Category.create(description='No name category')
    
    def test_category_str_representation(self):
        '''Test string representation of category'''
        category = Category.create(name='Technology')
        assert str(category) == 'Technology'


class TestFeed:
    '''Test Feed model'''
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        '''Setup test database for each test'''
        models = [Category, Feed, Filter, SchemaVersion]
        test_db.bind(models)
        test_db.connect()
        test_db.create_tables(models)
        
        yield
        
        test_db.drop_tables(models)
        test_db.close()
    
    @pytest.fixture
    def sample_category(self):
        '''Create a sample category for testing'''
        return Category.create(name='Technology')
    
    def test_feed_creation(self, sample_category):
        '''Test creating a feed'''
        feed = Feed.create(
            url='https://example.com/rss.xml',
            title='Example RSS Feed',
            description='A sample RSS feed',
            category=sample_category,
            fetch_interval=1800
        )
        
        assert feed.id is not None
        assert feed.url == 'https://example.com/rss.xml'
        assert feed.title == 'Example RSS Feed'
        assert feed.description == 'A sample RSS feed'
        assert feed.category.id == sample_category.id
        assert feed.is_active is True  # Default value
        assert feed.fetch_interval == 1800
        assert isinstance(feed.created_at, datetime)
        assert isinstance(feed.updated_at, datetime)
    
    def test_feed_url_unique(self, sample_category):
        '''Test that feed URLs must be unique'''
        url = 'https://example.com/rss.xml'
        Feed.create(url=url, category=sample_category)
        
        with pytest.raises(IntegrityError):
            Feed.create(url=url, category=sample_category)
    
    def test_feed_required_fields(self):
        '''Test that URL is required'''
        with pytest.raises(IntegrityError):
            Feed.create(title='No URL feed')
    
    def test_feed_default_values(self, sample_category):
        '''Test default values for feed fields'''
        feed = Feed.create(
            url='https://example.com/rss.xml',
            category=sample_category
        )
        
        assert feed.is_active is True
        assert feed.fetch_interval == 3600  # Default from settings
        assert feed.last_fetched is None
    
    def test_feed_category_relationship(self, sample_category):
        '''Test feed-category relationship'''
        feed = Feed.create(
            url='https://example.com/rss.xml',
            category=sample_category
        )
        
        assert feed.category.name == sample_category.name
        assert feed in sample_category.feeds
    
    def test_feed_category_deletion_handling(self, sample_category):
        '''Test that feed category is set to NULL when category is deleted'''
        feed = Feed.create(
            url='https://example.com/rss.xml',
            category=sample_category
        )
        
        sample_category.delete_instance()
        
        # Reload feed from database
        feed = Feed.get_by_id(feed.id)
        assert feed.category is None
    
    def test_feed_str_representation(self, sample_category):
        '''Test string representation of feed'''
        feed = Feed.create(
            url='https://example.com/rss.xml',
            title='Example Feed',
            category=sample_category
        )
        assert str(feed) == 'Example Feed'
    
    def test_feed_without_title_str_representation(self, sample_category):
        '''Test string representation when title is None'''
        feed = Feed.create(
            url='https://example.com/rss.xml',
            category=sample_category
        )
        assert str(feed) == 'https://example.com/rss.xml'


class TestFilter:
    '''Test Filter model'''
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        '''Setup test database for each test'''
        models = [Category, Feed, Filter, SchemaVersion]
        test_db.bind(models)
        test_db.connect()
        test_db.create_tables(models)
        
        yield
        
        test_db.drop_tables(models)
        test_db.close()
    
    def test_filter_creation(self):
        '''Test creating a filter'''
        criteria = {'keywords': ['python', 'programming'], 'exclude': ['beginner']}
        filter_obj = Filter.create(
            name='Python Advanced',
            type='keyword',
            criteria=json.dumps(criteria)
        )
        
        assert filter_obj.id is not None
        assert filter_obj.name == 'Python Advanced'
        assert filter_obj.type == 'keyword'
        assert json.loads(filter_obj.criteria) == criteria
        assert filter_obj.is_active is True  # Default value
        assert isinstance(filter_obj.created_at, datetime)
        assert isinstance(filter_obj.updated_at, datetime)
    
    def test_filter_required_fields(self):
        '''Test that required fields are enforced'''
        with pytest.raises(IntegrityError):
            Filter.create(type='keyword', criteria='{}')  # Missing name
        
        with pytest.raises(IntegrityError):
            Filter.create(name='Test', criteria='{}')  # Missing type
        
        with pytest.raises(IntegrityError):
            Filter.create(name='Test', type='keyword')  # Missing criteria
    
    def test_filter_default_values(self):
        '''Test default values for filter fields'''
        filter_obj = Filter.create(
            name='Test Filter',
            type='keyword',
            criteria='{}'
        )
        
        assert filter_obj.is_active is True
    
    def test_filter_str_representation(self):
        '''Test string representation of filter'''
        filter_obj = Filter.create(
            name='Test Filter',
            type='keyword',
            criteria='{}'
        )
        assert str(filter_obj) == 'Test Filter (keyword)'


class TestSchemaVersion:
    '''Test SchemaVersion model'''
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        '''Setup test database for each test'''
        models = [Category, Feed, Filter, SchemaVersion]
        test_db.bind(models)
        test_db.connect()
        test_db.create_tables(models)
        
        yield
        
        test_db.drop_tables(models)
        test_db.close()
    
    def test_schema_version_creation(self):
        '''Test creating a schema version record'''
        version = SchemaVersion.create(
            version=1,
            description='Initial schema creation'
        )
        
        assert version.id is not None
        assert version.version == 1
        assert version.description == 'Initial schema creation'
        assert isinstance(version.applied_at, datetime)
    
    def test_schema_version_unique(self):
        '''Test that version numbers must be unique'''
        SchemaVersion.create(version=1, description='First')
        
        with pytest.raises(IntegrityError):
            SchemaVersion.create(version=1, description='Duplicate')
    
    def test_schema_version_required_fields(self):
        '''Test that version is required'''
        with pytest.raises(IntegrityError):
            SchemaVersion.create(description='No version')
    
    def test_get_current_version(self):
        '''Test getting current schema version'''
        SchemaVersion.create(version=1, description='First')
        SchemaVersion.create(version=2, description='Second')
        SchemaVersion.create(version=3, description='Third')
        
        current = SchemaVersion.get_current_version()
        assert current == 3
    
    def test_get_current_version_empty(self):
        '''Test getting current version when no versions exist'''
        current = SchemaVersion.get_current_version()
        assert current == 0
    
    def test_schema_version_str_representation(self):
        '''Test string representation of schema version'''
        version = SchemaVersion.create(
            version=1,
            description='Initial schema'
        )
        assert str(version) == 'Schema Version 1: Initial schema'