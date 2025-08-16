import json
from datetime import datetime
from peewee import (
    AutoField, CharField, TextField, BooleanField, IntegerField, 
    DateTimeField, ForeignKeyField, DeferredForeignKey
)
from app.core.database import BaseModel
from app.core.config import settings


class ImportJob(BaseModel):
    '''Import job model for tracking OPML import operations'''
    
    id = CharField(primary_key=True)  # Format: 'imp_' + random string
    user_id = IntegerField()  # Future-proofing for user authentication
    filename = CharField(max_length=255)
    file_size = IntegerField()
    status = CharField(max_length=20, default='pending')  # pending, processing, completed, failed, cancelled
    duplicate_strategy = CharField(max_length=20, default='skip')  # skip, update, merge, prompt
    category_parent = DeferredForeignKey('Category', null=True, on_delete='SET NULL')
    validate_feeds = BooleanField(default=True)
    
    # Progress tracking
    total_steps = IntegerField(default=0)
    current_step = IntegerField(default=0)
    current_phase = CharField(max_length=50, null=True)  # parsing, creating_categories, validating_feeds, importing_feeds
    
    # Results summary
    categories_created = IntegerField(default=0)
    feeds_imported = IntegerField(default=0)
    feeds_failed = IntegerField(default=0)
    duplicates_found = IntegerField(default=0)
    
    # Timestamps
    created_at = DateTimeField(default=datetime.now)
    started_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
    
    # Error information
    error_message = TextField(null=True)
    error_details = TextField(null=True)
    
    class Meta:
        table_name = 'import_jobs'
        indexes = (
            (('user_id',), False),
            (('status',), False),
            (('created_at',), False),
        )
    
    def __str__(self):
        return f'Import {self.id}: {self.filename} ({self.status})'


class Category(BaseModel):
    '''Category model for organizing RSS feeds'''
    
    id = AutoField()
    name = CharField(max_length=100, unique=True)
    description = TextField(null=True)
    color = CharField(max_length=7, null=True)  # Hex color code
    import_job = ForeignKeyField(ImportJob, null=True, on_delete='SET NULL')  # Track import source
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'categories'
        indexes = (
            (('name',), True),  # Unique index on name
            (('import_job',), False),  # Index for import tracking
        )
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        '''Override save to update timestamp'''
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class Feed(BaseModel):
    '''Feed model for RSS/Atom feeds'''
    
    id = AutoField()
    url = CharField(max_length=500, unique=True)
    title = CharField(max_length=200, null=True)
    description = TextField(null=True)
    category = ForeignKeyField(
        Category, 
        backref='feeds', 
        null=True, 
        on_delete='SET NULL'
    )
    is_active = BooleanField(default=True)
    fetch_interval = IntegerField(default=lambda: settings.default_feed_update_interval)
    last_fetched = DateTimeField(null=True)
    
    # Import metadata
    import_job = ForeignKeyField(ImportJob, null=True, on_delete='SET NULL')  # Track import source
    opml_title = CharField(max_length=255, null=True)  # Original title from OPML
    opml_description = TextField(null=True)  # Original description from OPML
    opml_html_url = CharField(max_length=500, null=True)  # HTML URL from OPML
    
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'feeds'
        indexes = (
            (('url',), True),  # Unique index on URL
            (('category',), False),  # Index on category for faster lookups
            (('is_active',), False),  # Index on active status
            (('import_job',), False),  # Index for import tracking
        )
    
    def __str__(self):
        return self.title or self.url
    
    def save(self, *args, **kwargs):
        '''Override save to update timestamp'''
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class Filter(BaseModel):
    '''Filter model for content filtering rules'''
    
    id = AutoField()
    name = CharField(max_length=100)
    type = CharField(max_length=50)  # 'keyword', 'regex', 'category', etc.
    criteria = TextField()  # JSON string with filter criteria
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'filters'
        indexes = (
            (('type',), False),  # Index on filter type
            (('is_active',), False),  # Index on active status
        )
    
    def __str__(self):
        return f'{self.name} ({self.type})'
    
    def get_criteria_dict(self):
        '''Parse criteria JSON string to dictionary'''
        try:
            return json.loads(self.criteria)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_criteria_dict(self, criteria_dict):
        '''Set criteria from dictionary'''
        self.criteria = json.dumps(criteria_dict)
    
    def save(self, *args, **kwargs):
        '''Override save to update timestamp'''
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class SchemaVersion(BaseModel):
    '''Schema version tracking for database migrations'''
    
    id = AutoField()
    version = IntegerField(unique=True)
    applied_at = DateTimeField(default=datetime.now)
    description = TextField(null=True)
    
    class Meta:
        table_name = 'schema_version'
        indexes = (
            (('version',), True),  # Unique index on version
        )
    
    def __str__(self):
        return f'Schema Version {self.version}: {self.description or "No description"}'
    
    @classmethod
    def get_current_version(cls):
        '''Get the current schema version'''
        try:
            latest = cls.select().order_by(cls.version.desc()).get()
            return latest.version
        except cls.DoesNotExist:
            return 0
    
    @classmethod
    def is_version_applied(cls, version):
        '''Check if a specific version has been applied'''
        try:
            cls.get(cls.version == version)
            return True
        except cls.DoesNotExist:
            return False


class ImportResult(BaseModel):
    '''Import result model for detailed results of each imported item'''
    
    id = AutoField()
    import_job = ForeignKeyField(ImportJob, backref='results', on_delete='CASCADE')
    item_type = CharField(max_length=20)  # category, feed
    item_name = CharField(max_length=255)
    item_url = CharField(max_length=500, null=True)  # NULL for categories
    status = CharField(max_length=30)  # success, failed, duplicate_skipped, duplicate_updated, duplicate_merged
    error_message = TextField(null=True)
    error_code = CharField(max_length=50, null=True)
    
    # References to created items
    created_category = DeferredForeignKey('Category', null=True, on_delete='SET NULL')
    created_feed = DeferredForeignKey('Feed', null=True, on_delete='SET NULL')
    existing_item_id = IntegerField(null=True)  # For duplicate handling
    
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'import_results'
        indexes = (
            (('import_job',), False),
            (('status',), False),
            (('item_type',), False),
            (('import_job', 'item_type', 'item_name'), False),
        )
    
    def __str__(self):
        return f'{self.item_type}: {self.item_name} ({self.status})'


class ImportFeedValidation(BaseModel):
    '''Feed validation cache to avoid duplicate validation requests'''
    
    id = AutoField()
    feed_url = CharField(max_length=500, unique=True)
    is_valid = BooleanField()
    final_url = CharField(max_length=500, null=True)  # After redirects
    title = CharField(max_length=255, null=True)
    description = TextField(null=True)
    feed_type = CharField(max_length=20, null=True)  # rss, atom, unknown
    error_message = TextField(null=True)
    error_code = CharField(max_length=50, null=True)
    validated_at = DateTimeField(default=datetime.now)
    expires_at = DateTimeField(null=True)  # Cache expiration
    
    class Meta:
        table_name = 'import_feed_validation'
        indexes = (
            (('feed_url',), True),  # Unique index on feed_url
            (('expires_at',), False),
        )
    
    def __str__(self):
        return f'Validation: {self.feed_url} ({"valid" if self.is_valid else "invalid"})'


# Model registry for easy access
ALL_MODELS = [Category, Feed, Filter, SchemaVersion, ImportJob, ImportResult, ImportFeedValidation]

# Import article models to make them available
from app.models.article import ARTICLE_MODELS
ALL_MODELS.extend(ARTICLE_MODELS)