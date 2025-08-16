import pytest
import json
from datetime import datetime
from peewee import IntegrityError, SqliteDatabase
from app.core.database import BaseModel
from app.models.base import Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation


# Test database for isolated testing
test_db = SqliteDatabase(':memory:', pragmas={'foreign_keys': 1})


class TestBaseModel:
    '''Test base model functionality'''
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        '''Setup test database for each test'''
        # Bind models to test database
        models = [Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation]
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
        models = [Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation]
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
        models = [Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation]
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
        models = [Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation]
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
        models = [Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation]
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


class TestImportJob:
    '''Test ImportJob model'''
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        '''Setup test database for each test'''
        models = [Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation]
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
    
    def test_import_job_creation(self, sample_category):
        '''Test creating an import job'''
        job = ImportJob.create(
            id='imp_test123',
            user_id=1,
            filename='test_feeds.opml',
            file_size=1024,
            status='pending',
            duplicate_strategy='skip',
            category_parent=sample_category,
            validate_feeds=True
        )
        
        assert job.id == 'imp_test123'
        assert job.user_id == 1
        assert job.filename == 'test_feeds.opml'
        assert job.file_size == 1024
        assert job.status == 'pending'
        assert job.duplicate_strategy == 'skip'
        assert job.category_parent.id == sample_category.id
        assert job.validate_feeds is True
        assert job.total_steps == 0  # Default value
        assert job.current_step == 0  # Default value
        assert isinstance(job.created_at, datetime)
    
    def test_import_job_default_values(self):
        '''Test default values for import job fields'''
        job = ImportJob.create(
            id='imp_test456',
            user_id=1,
            filename='test.opml',
            file_size=512
        )
        
        assert job.status == 'pending'
        assert job.duplicate_strategy == 'skip'
        assert job.validate_feeds is True
        assert job.total_steps == 0
        assert job.current_step == 0
        assert job.categories_created == 0
        assert job.feeds_imported == 0
        assert job.feeds_failed == 0
        assert job.duplicates_found == 0
        assert job.started_at is None
        assert job.completed_at is None
        assert job.error_message is None
        assert job.error_details is None
    
    def test_import_job_required_fields(self):
        '''Test that required fields are enforced'''
        with pytest.raises(IntegrityError):
            ImportJob.create(  # Missing id (primary key)
                user_id=1,
                filename='test.opml',
                file_size=512
            )
        
        with pytest.raises(IntegrityError):
            ImportJob.create(
                id='imp_test789',
                filename='test.opml',  # Missing user_id
                file_size=512
            )
    
    def test_import_job_str_representation(self):
        '''Test string representation of import job'''
        job = ImportJob.create(
            id='imp_test123',
            user_id=1,
            filename='my_feeds.opml',
            file_size=1024,
            status='processing'
        )
        assert str(job) == 'Import imp_test123: my_feeds.opml (processing)'


class TestImportResult:
    '''Test ImportResult model'''
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        '''Setup test database for each test'''
        models = [Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation]
        test_db.bind(models)
        test_db.connect()
        test_db.create_tables(models)
        
        yield
        
        test_db.drop_tables(models)
        test_db.close()
    
    @pytest.fixture
    def sample_import_job(self):
        '''Create a sample import job for testing'''
        return ImportJob.create(
            id='imp_test123',
            user_id=1,
            filename='test.opml',
            file_size=1024
        )
    
    @pytest.fixture
    def sample_category(self):
        '''Create a sample category for testing'''
        return Category.create(name='Technology')
    
    @pytest.fixture
    def sample_feed(self, sample_category):
        '''Create a sample feed for testing'''
        return Feed.create(
            url='https://example.com/feed.xml',
            title='Example Feed',
            category=sample_category
        )
    
    def test_import_result_creation(self, sample_import_job, sample_category):
        '''Test creating an import result'''
        result = ImportResult.create(
            import_job=sample_import_job,
            item_type='category',
            item_name='Technology',
            status='success',
            created_category=sample_category
        )
        
        assert result.id is not None
        assert result.import_job.id == sample_import_job.id
        assert result.item_type == 'category'
        assert result.item_name == 'Technology'
        assert result.item_url is None
        assert result.status == 'success'
        assert result.created_category.id == sample_category.id
        assert result.created_feed is None
        assert result.existing_item_id is None
        assert isinstance(result.created_at, datetime)
    
    def test_import_result_feed_creation(self, sample_import_job, sample_feed):
        '''Test creating an import result for a feed'''
        result = ImportResult.create(
            import_job=sample_import_job,
            item_type='feed',
            item_name='Example Feed',
            item_url='https://example.com/feed.xml',
            status='success',
            created_feed=sample_feed
        )
        
        assert result.item_type == 'feed'
        assert result.item_name == 'Example Feed'
        assert result.item_url == 'https://example.com/feed.xml'
        assert result.created_feed.id == sample_feed.id
    
    def test_import_result_error_handling(self, sample_import_job):
        '''Test creating an import result with error information'''
        result = ImportResult.create(
            import_job=sample_import_job,
            item_type='feed',
            item_name='Broken Feed',
            item_url='https://broken.example.com/feed.xml',
            status='failed',
            error_message='Feed URL not found',
            error_code='404'
        )
        
        assert result.status == 'failed'
        assert result.error_message == 'Feed URL not found'
        assert result.error_code == '404'
        assert result.created_category is None
        assert result.created_feed is None
    
    def test_import_result_duplicate_handling(self, sample_import_job, sample_feed):
        '''Test import result for duplicate handling'''
        result = ImportResult.create(
            import_job=sample_import_job,
            item_type='feed',
            item_name='Duplicate Feed',
            item_url='https://example.com/feed.xml',
            status='duplicate_skipped',
            existing_item_id=sample_feed.id
        )
        
        assert result.status == 'duplicate_skipped'
        assert result.existing_item_id == sample_feed.id
    
    def test_import_result_required_fields(self, sample_import_job):
        '''Test that required fields are enforced'''
        with pytest.raises(IntegrityError):
            ImportResult.create(  # Missing import_job
                item_type='feed',
                item_name='Test Feed',
                status='success'
            )
        
        with pytest.raises(IntegrityError):
            ImportResult.create(
                import_job=sample_import_job,
                item_name='Test Feed',  # Missing item_type
                status='success'
            )
    
    def test_import_result_str_representation(self, sample_import_job):
        '''Test string representation of import result'''
        result = ImportResult.create(
            import_job=sample_import_job,
            item_type='feed',
            item_name='Example Feed',
            status='success'
        )
        assert str(result) == 'feed: Example Feed (success)'


class TestImportFeedValidation:
    '''Test ImportFeedValidation model'''
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        '''Setup test database for each test'''
        models = [Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation]
        test_db.bind(models)
        test_db.connect()
        test_db.create_tables(models)
        
        yield
        
        test_db.drop_tables(models)
        test_db.close()
    
    def test_feed_validation_creation(self):
        '''Test creating a feed validation record'''
        validation = ImportFeedValidation.create(
            feed_url='https://example.com/feed.xml',
            is_valid=True,
            final_url='https://example.com/feed.xml',
            title='Example Feed',
            description='A sample RSS feed',
            feed_type='rss'
        )
        
        assert validation.id is not None
        assert validation.feed_url == 'https://example.com/feed.xml'
        assert validation.is_valid is True
        assert validation.final_url == 'https://example.com/feed.xml'
        assert validation.title == 'Example Feed'
        assert validation.description == 'A sample RSS feed'
        assert validation.feed_type == 'rss'
        assert validation.error_message is None
        assert validation.error_code is None
        assert isinstance(validation.validated_at, datetime)
        assert validation.expires_at is None  # Optional field
    
    def test_feed_validation_invalid_feed(self):
        '''Test creating a validation record for an invalid feed'''
        validation = ImportFeedValidation.create(
            feed_url='https://invalid.example.com/feed.xml',
            is_valid=False,
            error_message='Feed not found',
            error_code='404'
        )
        
        assert validation.is_valid is False
        assert validation.final_url is None
        assert validation.title is None
        assert validation.description is None
        assert validation.feed_type is None
        assert validation.error_message == 'Feed not found'
        assert validation.error_code == '404'
    
    def test_feed_validation_url_unique(self):
        '''Test that feed URLs must be unique in validation cache'''
        url = 'https://example.com/feed.xml'
        ImportFeedValidation.create(
            feed_url=url,
            is_valid=True
        )
        
        with pytest.raises(IntegrityError):
            ImportFeedValidation.create(
                feed_url=url,
                is_valid=False
            )
    
    def test_feed_validation_required_fields(self):
        '''Test that required fields are enforced'''
        with pytest.raises(IntegrityError):
            ImportFeedValidation.create(  # Missing feed_url
                is_valid=True
            )
        
        with pytest.raises(IntegrityError):
            ImportFeedValidation.create(
                feed_url='https://example.com/feed.xml'
                # Missing is_valid
            )
    
    def test_feed_validation_str_representation(self):
        '''Test string representation of feed validation'''
        validation = ImportFeedValidation.create(
            feed_url='https://example.com/feed.xml',
            is_valid=True
        )
        assert str(validation) == 'Validation: https://example.com/feed.xml (valid)'
    
    def test_feed_validation_invalid_str_representation(self):
        '''Test string representation for invalid feed validation'''
        validation = ImportFeedValidation.create(
            feed_url='https://invalid.example.com/feed.xml',
            is_valid=False
        )
        assert str(validation) == 'Validation: https://invalid.example.com/feed.xml (invalid)'


class TestImportModelRelationships:
    '''Test relationships between import models and existing models'''
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        '''Setup test database for each test'''
        models = [Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation]
        test_db.bind(models)
        test_db.connect()
        test_db.create_tables(models)
        
        yield
        
        test_db.drop_tables(models)
        test_db.close()
    
    def test_category_import_tracking(self):
        '''Test tracking import source in categories'''
        job = ImportJob.create(
            id='imp_test123',
            user_id=1,
            filename='test.opml',
            file_size=1024
        )
        
        category = Category.create(
            name='Imported Category',
            import_job=job
        )
        
        assert category.import_job.id == job.id
    
    def test_feed_import_tracking(self):
        '''Test tracking import source and OPML metadata in feeds'''
        job = ImportJob.create(
            id='imp_test123',
            user_id=1,
            filename='test.opml',
            file_size=1024
        )
        
        category = Category.create(name='Technology')
        
        feed = Feed.create(
            url='https://example.com/feed.xml',
            title='Processed Title',
            description='Processed Description',
            category=category,
            import_job=job,
            opml_title='Original OPML Title',
            opml_description='Original OPML Description',
            opml_html_url='https://example.com/'
        )
        
        assert feed.import_job.id == job.id
        assert feed.opml_title == 'Original OPML Title'
        assert feed.opml_description == 'Original OPML Description'
        assert feed.opml_html_url == 'https://example.com/'
    
    def test_import_job_cascade_deletion(self):
        '''Test that import results are deleted when import job is deleted'''
        job = ImportJob.create(
            id='imp_test123',
            user_id=1,
            filename='test.opml',
            file_size=1024
        )
        
        result = ImportResult.create(
            import_job_id=job.id,
            item_type='feed',
            item_name='Test Feed',
            status='success'
        )
        
        # Delete the import job
        job.delete_instance()
        
        # Check that the import result was also deleted (CASCADE)
        with pytest.raises(ImportResult.DoesNotExist):
            ImportResult.get_by_id(result.id)
    
    def test_category_deletion_handling_in_import_job(self):
        '''Test that import job can reference a category and handle relationship'''
        category = Category.create(name='Parent Category')
        
        job = ImportJob.create(
            id='imp_test123',
            user_id=1,
            filename='test.opml',
            file_size=1024,
            category_parent=category
        )
        
        # Test that the relationship works
        assert job.category_parent.id == category.id
        assert job.category_parent.name == 'Parent Category'
        
        # Test setting to None
        job.category_parent = None
        job.save()
        
        # Reload job from database
        job = ImportJob.get_by_id(job.id)
        assert job.category_parent is None