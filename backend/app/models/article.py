import re
from datetime import datetime
from typing import List, Optional
from peewee import (
    AutoField, CharField, TextField, BooleanField, IntegerField, 
    DateTimeField, ForeignKeyField, DoesNotExist
)
from app.core.database import BaseModel
from app.models.base import Feed


class Article(BaseModel):
    '''Article model for storing RSS/Atom feed articles'''
    
    id = AutoField()
    feed = ForeignKeyField(Feed, backref='articles', on_delete='CASCADE')
    
    # Article content
    title = CharField(max_length=500, null=True)
    content = TextField(null=True)  # Full article content (HTML)
    summary = TextField(null=True)  # Article summary/description
    url = CharField(max_length=1000)  # Article URL
    guid = CharField(max_length=500)  # Article GUID from feed
    
    # Article metadata
    author = CharField(max_length=200, null=True)
    published_date = DateTimeField(null=True)  # When article was published
    tags = CharField(max_length=1000, null=True)  # Comma-separated tags
    image_url = CharField(max_length=1000, null=True)  # Article thumbnail/image URL
    
    # System metadata
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'articles'
        indexes = (
            # Unique constraint on feed + URL
            (('feed', 'url'), True),
            # Unique constraint on feed + GUID  
            (('feed', 'guid'), True),
            # Performance indexes
            (('feed', 'published_date'), False),
            (('published_date',), False),
            (('created_at',), False),
            (('feed', 'created_at'), False),
        )
    
    def __str__(self):
        return self.title or self.url
    
    def save(self, *args, **kwargs):
        '''Override save to update timestamp'''
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def get_tag_list(self) -> List[str]:
        '''Parse tags string into list of tags'''
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def set_tag_list(self, tags: List[str]):
        '''Set tags from list of strings'''
        if tags:
            self.tags = ','.join(tag.strip() for tag in tags if tag.strip())
        else:
            self.tags = None
    
    def get_word_count(self) -> int:
        '''Calculate word count from content (stripping HTML)'''
        if not self.content:
            return 0
        
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', ' ', self.content)
        # Split into words and count
        words = re.findall(r'\b\w+\b', text.lower())
        return len(words)
    
    def get_estimated_reading_time(self, words_per_minute: int = 200) -> int:
        '''Estimate reading time in minutes'''
        word_count = self.get_word_count()
        if word_count == 0:
            return 0
        return max(1, round(word_count / words_per_minute))
    
    def sanitize_content(self):
        '''Sanitize HTML content to remove dangerous elements'''
        if not self.content:
            return
        
        try:
            import bleach
            
            # Allow safe HTML tags and attributes
            allowed_tags = [
                'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'ul', 'ol', 'li',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre',
                'a', 'img', 'div', 'span', 'table', 'thead', 'tbody', 'tr', 'td', 'th'
            ]
            
            allowed_attributes = {
                'a': ['href', 'title'],
                'img': ['src', 'alt', 'title', 'width', 'height'],
                'blockquote': ['cite'],
                '*': ['class']  # Allow class attribute on all elements
            }
            
            # Sanitize content
            self.content = bleach.clean(
                self.content,
                tags=allowed_tags,
                attributes=allowed_attributes,
                strip=True
            )
            
            # Also sanitize summary if it exists
            if self.summary:
                self.summary = bleach.clean(
                    self.summary,
                    tags=['p', 'br', 'strong', 'b', 'em', 'i'],
                    attributes={},
                    strip=True
                )
        except ImportError:
            # If bleach is not available, log warning but continue
            # In production, this should be a hard requirement
            pass
    
    @classmethod
    def _extract_image_url(cls, entry: dict) -> Optional[str]:
        '''Extract image URL from feed entry'''
        # Check for media:content or media:thumbnail (in dict format)
        media_content = entry.get('media_content')
        if media_content:
            for media in media_content:
                if media.get('type', '').startswith('image/'):
                    return media.get('url')
        
        media_thumbnail = entry.get('media_thumbnail')
        if media_thumbnail and isinstance(media_thumbnail, list):
            return media_thumbnail[0].get('url')
        
        # Check for enclosures (common in podcasts but sometimes used for images)
        enclosures = entry.get('enclosures')
        if enclosures:
            for enclosure in enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    return enclosure.get('href') or enclosure.get('url')
        
        # Check for image in links (some feeds use this)
        links = entry.get('links')
        if links:
            for link in links:
                if link.get('type', '').startswith('image/'):
                    return link.get('href')
                # Also check for rel="enclosure" with image type
                if link.get('rel') == 'enclosure' and link.get('type', '').startswith('image/'):
                    return link.get('href')
        
        # Try to extract from content HTML (first img tag)
        content = entry.get('content') or entry.get('description') or entry.get('summary')
        if content:
            import re
            # Look for img tag with src attribute
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', str(content), re.IGNORECASE)
            if img_match:
                return img_match.group(1)
        
        return None
    
    @classmethod
    def find_duplicate(cls, feed: Feed, url: str, guid: str) -> Optional['Article']:
        '''Find duplicate article by URL or GUID within the same feed'''
        try:
            # First try to find by URL
            return cls.get((cls.feed == feed) & (cls.url == url))
        except DoesNotExist:
            pass
        
        try:
            # Then try to find by GUID
            return cls.get((cls.feed == feed) & (cls.guid == guid))
        except DoesNotExist:
            pass
        
        return None
    
    @classmethod
    def create_from_feed_entry(cls, feed: Feed, entry: dict, **kwargs) -> 'Article':
        '''Create article from parsed feed entry data'''
        # Extract basic fields
        article_data = {
            'feed': feed,
            'title': entry.get('title'),
            'content': entry.get('content') or entry.get('description'),
            'summary': entry.get('summary'),
            'url': entry.get('link'),
            'guid': entry.get('id') or entry.get('guid') or entry.get('link'),
            'author': entry.get('author'),
            'tags': ','.join(entry.get('tags', [])) if entry.get('tags') else None,
            'image_url': cls._extract_image_url(entry),
        }
        
        # Parse published date
        if entry.get('published_parsed'):
            try:
                import time
                article_data['published_date'] = datetime.fromtimestamp(
                    time.mktime(entry['published_parsed'])
                )
            except (ValueError, TypeError, OverflowError):
                pass
        
        # Merge with any additional kwargs
        article_data.update(kwargs)
        
        # Create and return article
        article = cls.create(**article_data)
        article.sanitize_content()
        return article


class User(BaseModel):
    '''User model for authentication and personalization'''
    
    id = AutoField()
    username = CharField(max_length=50, unique=True)
    email = CharField(max_length=254, unique=True)
    password_hash = CharField(max_length=255)  # Hashed password
    
    # User preferences
    is_active = BooleanField(default=True)
    feeds_per_page = IntegerField(default=50)  # Articles per page preference
    default_view = CharField(max_length=20, default='unread')  # unread, all, starred
    
    # Article display preferences
    open_webpage_for_short_articles = BooleanField(default=False)  # Open webpage instead of modal for short articles
    short_article_threshold = IntegerField(default=500)  # Character count threshold for short articles
    show_timestamps_in_list = BooleanField(default=True)  # Show relative timestamps in article list
    preferred_view_mode = CharField(max_length=10, default='list')  # 'list' or 'card' view mode
    
    # Feed refresh preferences
    auto_refresh_feeds = BooleanField(default=False)  # Auto-refresh feeds periodically
    auto_refresh_interval_minutes = IntegerField(default=30)  # Auto-refresh interval in minutes
    
    # Timestamps
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    last_login = DateTimeField(null=True)
    
    class Meta:
        table_name = 'users'
        indexes = (
            (('username',), True),
            (('email',), True),
            (('is_active',), False),
        )
    
    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        '''Override save to update timestamp'''
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class UserSubscription(BaseModel):
    '''User subscription to feeds for personalized feed management'''
    
    id = AutoField()
    user = ForeignKeyField(User, backref='subscriptions', on_delete='CASCADE')
    feed = ForeignKeyField(Feed, backref='subscribers', on_delete='CASCADE')
    
    # Subscription settings
    is_active = BooleanField(default=True)
    custom_title = CharField(max_length=200, null=True)  # User's custom feed title
    notification_enabled = BooleanField(default=False)
    
    # Timestamps
    subscribed_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'user_subscriptions'
        indexes = (
            # Unique constraint - user can only subscribe to a feed once
            (('user', 'feed'), True),
            (('user', 'is_active'), False),
            (('subscribed_at',), False),
        )
    
    def __str__(self):
        return f'{self.user.username} -> {self.feed.title}'
    
    def save(self, *args, **kwargs):
        '''Override save to update timestamp'''
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class ReadStatus(BaseModel):
    '''Track read/unread status of articles for users'''
    
    id = AutoField()
    user = ForeignKeyField(User, backref='read_statuses', on_delete='CASCADE')
    article = ForeignKeyField(Article, backref='read_statuses', on_delete='CASCADE')
    
    # Status information
    is_read = BooleanField(default=False)
    is_starred = BooleanField(default=False)  # Bookmarked/favorited
    is_archived = BooleanField(default=False)  # Hidden from main view
    
    # Timestamps
    read_at = DateTimeField(null=True)  # When article was marked as read
    starred_at = DateTimeField(null=True)  # When article was starred
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'read_statuses'
        indexes = (
            # Unique constraint - one status record per user-article pair
            (('user', 'article'), True),
            # Performance indexes for common queries
            (('user', 'is_read'), False),
            (('user', 'is_starred'), False),
            (('user', 'is_archived'), False),
            (('user', 'is_read', 'is_archived'), False),
            (('article', 'is_read'), False),
            (('read_at',), False),
        )
    
    def __str__(self):
        status = []
        if self.is_read:
            status.append('read')
        if self.is_starred:
            status.append('starred') 
        if self.is_archived:
            status.append('archived')
        
        status_str = ', '.join(status) if status else 'unread'
        return f'{self.user.username}: {self.article.title} ({status_str})'
    
    def save(self, *args, **kwargs):
        '''Override save to update timestamp and set read_at'''
        self.updated_at = datetime.now()
        
        # Set read_at timestamp when marking as read
        if self.is_read and not self.read_at:
            self.read_at = datetime.now()
        # Clear read_at when marking as unread
        elif not self.is_read and self.read_at:
            self.read_at = None
            
        # Set starred_at timestamp when starring
        if self.is_starred and not self.starred_at:
            self.starred_at = datetime.now()
        # Clear starred_at when unstarring
        elif not self.is_starred and self.starred_at:
            self.starred_at = None
        
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_or_create_for_user_article(cls, user: User, article: Article) -> 'ReadStatus':
        '''Get existing read status or create new one for user-article pair'''
        try:
            return cls.get((cls.user == user) & (cls.article == article))
        except DoesNotExist:
            return cls.create(user=user, article=article)
    
    @classmethod
    def mark_read(cls, user: User, article: Article, is_read: bool = True) -> 'ReadStatus':
        '''Mark article as read/unread for user'''
        status = cls.get_or_create_for_user_article(user, article)
        status.is_read = is_read
        status.save()
        return status
    
    @classmethod
    def mark_starred(cls, user: User, article: Article, is_starred: bool = True) -> 'ReadStatus':
        '''Mark article as starred/unstarred for user'''
        status = cls.get_or_create_for_user_article(user, article)
        status.is_starred = is_starred
        status.save()
        return status


# Update the model registry
ARTICLE_MODELS = [User, Article, UserSubscription, ReadStatus]