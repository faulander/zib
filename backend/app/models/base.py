import json
from datetime import datetime
from peewee import (
    AutoField, CharField, TextField, BooleanField, IntegerField, 
    DateTimeField, ForeignKeyField
)
from app.core.database import BaseModel
from app.core.config import settings


class Category(BaseModel):
    '''Category model for organizing RSS feeds'''
    
    id = AutoField()
    name = CharField(max_length=100, unique=True)
    description = TextField(null=True)
    color = CharField(max_length=7, null=True)  # Hex color code
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'categories'
        indexes = (
            (('name',), True),  # Unique index on name
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
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'feeds'
        indexes = (
            (('url',), True),  # Unique index on URL
            (('category',), False),  # Index on category for faster lookups
            (('is_active',), False),  # Index on active status
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


# Model registry for easy access
ALL_MODELS = [Category, Feed, Filter, SchemaVersion]