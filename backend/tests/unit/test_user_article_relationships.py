import pytest
from datetime import datetime, timedelta
from peewee import IntegrityError
from app.models.article import User, Article, UserSubscription, ReadStatus
from app.models.base import Category, Feed
from app.core.database import db


class TestUserArticleRelationships:
    '''Test user-article relationship models'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database with all required tables'''
        models = [Category, Feed, User, Article, UserSubscription, ReadStatus]
        db.create_tables(models, safe=True)
        
        yield
        
        # Clean up after each test
        db.drop_tables(models, safe=True)
    
    @pytest.fixture
    def sample_user(self):
        '''Create a sample user for testing'''
        return User.create(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password_123',
            feeds_per_page=25,
            default_view='unread'
        )
    
    @pytest.fixture
    def sample_category(self):
        '''Create a sample category'''
        return Category.create(
            name='Technology',
            description='Tech news'
        )
    
    @pytest.fixture
    def sample_feed(self, sample_category):
        '''Create a sample feed'''
        return Feed.create(
            url='https://example.com/feed.xml',
            title='Tech Blog',
            description='A great tech blog',
            category=sample_category
        )
    
    @pytest.fixture
    def sample_article(self, sample_feed):
        '''Create a sample article'''
        return Article.create(
            feed=sample_feed,
            title='Test Article',
            content='<p>Test content</p>',
            url='https://example.com/article-1',
            guid='article-1-guid',
            published_date=datetime(2024, 1, 15, 10, 30, 0)
        )


class TestUserModel:
    '''Test User model functionality'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [User]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    def test_create_user_with_required_fields(self):
        '''Test creating a user with all required fields'''
        user = User.create(
            username='johndoe',
            email='john@example.com',
            password_hash='hashed_password_abc'
        )
        
        assert user.id is not None
        assert user.username == 'johndoe'
        assert user.email == 'john@example.com'
        assert user.password_hash == 'hashed_password_abc'
        assert user.is_active is True  # Default
        assert user.feeds_per_page == 50  # Default
        assert user.default_view == 'unread'  # Default
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.last_login is None
    
    def test_create_user_with_custom_preferences(self):
        '''Test creating a user with custom preferences'''
        user = User.create(
            username='janedoe',
            email='jane@example.com',
            password_hash='hashed_password_def',
            feeds_per_page=100,
            default_view='all',
            is_active=False
        )
        
        assert user.feeds_per_page == 100
        assert user.default_view == 'all'
        assert user.is_active is False
    
    def test_username_must_be_unique(self):
        '''Test that usernames must be unique'''
        User.create(
            username='duplicate',
            email='first@example.com',
            password_hash='password1'
        )
        
        with pytest.raises(IntegrityError):
            User.create(
                username='duplicate',
                email='second@example.com',
                password_hash='password2'
            )
    
    def test_email_must_be_unique(self):
        '''Test that emails must be unique'''
        User.create(
            username='user1',
            email='duplicate@example.com',
            password_hash='password1'
        )
        
        with pytest.raises(IntegrityError):
            User.create(
                username='user2',
                email='duplicate@example.com',
                password_hash='password2'
            )
    
    def test_user_string_representation(self):
        '''Test user string representation'''
        user = User.create(
            username='testuser',
            email='test@example.com',
            password_hash='password123'
        )
        
        assert str(user) == 'testuser'
    
    def test_user_save_updates_timestamp(self):
        '''Test that saving a user updates the updated_at timestamp'''
        user = User.create(
            username='timetest',
            email='time@example.com',
            password_hash='password123'
        )
        
        original_updated_at = user.updated_at
        
        import time
        time.sleep(0.01)
        
        user.email = 'newemail@example.com'
        user.save()
        
        assert user.updated_at > original_updated_at


class TestUserSubscriptionModel:
    '''Test UserSubscription model functionality'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [Category, Feed, User, UserSubscription]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    @pytest.fixture
    def sample_user(self):
        '''Create sample user'''
        return User.create(
            username='subscriber',
            email='subscriber@example.com',
            password_hash='password123'
        )
    
    @pytest.fixture
    def sample_feed(self):
        '''Create sample feed'''
        category = Category.create(name='News')
        return Feed.create(
            url='https://news.example.com/feed.xml',
            title='News Feed',
            category=category
        )
    
    def test_create_subscription(self, sample_user, sample_feed):
        '''Test creating a user subscription'''
        subscription = UserSubscription.create(
            user=sample_user,
            feed=sample_feed,
            is_active=True,
            custom_title='My Custom News',
            notification_enabled=True
        )
        
        assert subscription.id is not None
        assert subscription.user == sample_user
        assert subscription.feed == sample_feed
        assert subscription.is_active is True
        assert subscription.custom_title == 'My Custom News'
        assert subscription.notification_enabled is True
        assert subscription.subscribed_at is not None
        assert subscription.updated_at is not None
    
    def test_subscription_defaults(self, sample_user, sample_feed):
        '''Test subscription default values'''
        subscription = UserSubscription.create(
            user=sample_user,
            feed=sample_feed
        )
        
        assert subscription.is_active is True  # Default
        assert subscription.custom_title is None  # Default
        assert subscription.notification_enabled is False  # Default
    
    def test_user_can_only_subscribe_once_to_feed(self, sample_user, sample_feed):
        '''Test that a user can only subscribe once to the same feed'''
        UserSubscription.create(
            user=sample_user,
            feed=sample_feed
        )
        
        with pytest.raises(IntegrityError):
            UserSubscription.create(
                user=sample_user,
                feed=sample_feed
            )
    
    def test_subscription_relationships(self, sample_user, sample_feed):
        '''Test subscription relationships'''
        subscription = UserSubscription.create(
            user=sample_user,
            feed=sample_feed
        )
        
        # Test forward relationships
        assert subscription.user.username == 'subscriber'
        assert subscription.feed.title == 'News Feed'
        
        # Test reverse relationships (backrefs)
        user_subscriptions = list(sample_user.subscriptions)
        assert len(user_subscriptions) == 1
        assert user_subscriptions[0] == subscription
        
        feed_subscribers = list(sample_feed.subscribers)
        assert len(feed_subscribers) == 1
        assert feed_subscribers[0] == subscription
    
    def test_subscription_string_representation(self, sample_user, sample_feed):
        '''Test subscription string representation'''
        subscription = UserSubscription.create(
            user=sample_user,
            feed=sample_feed
        )
        
        assert str(subscription) == 'subscriber -> News Feed'
    
    def test_subscription_save_updates_timestamp(self, sample_user, sample_feed):
        '''Test that saving a subscription updates timestamp'''
        subscription = UserSubscription.create(
            user=sample_user,
            feed=sample_feed
        )
        
        original_updated_at = subscription.updated_at
        
        import time
        time.sleep(0.01)
        
        subscription.custom_title = 'Updated Title'
        subscription.save()
        
        assert subscription.updated_at > original_updated_at


class TestReadStatusModel:
    '''Test ReadStatus model functionality'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [Category, Feed, User, Article, ReadStatus]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    @pytest.fixture
    def sample_user(self):
        '''Create sample user'''
        return User.create(
            username='reader',
            email='reader@example.com',
            password_hash='password123'
        )
    
    @pytest.fixture
    def sample_article(self):
        '''Create sample article'''
        category = Category.create(name='Tech')
        feed = Feed.create(
            url='https://tech.example.com/feed.xml',
            title='Tech Feed',
            category=category
        )
        return Article.create(
            feed=feed,
            title='Sample Article',
            url='https://tech.example.com/article-1',
            guid='article-1-guid'
        )
    
    def test_create_read_status(self, sample_user, sample_article):
        '''Test creating a read status'''
        status = ReadStatus.create(
            user=sample_user,
            article=sample_article,
            is_read=True,
            is_starred=True,
            is_archived=False
        )
        
        assert status.id is not None
        assert status.user == sample_user
        assert status.article == sample_article
        assert status.is_read is True
        assert status.is_starred is True
        assert status.is_archived is False
        assert status.read_at is not None  # Set automatically when is_read=True
        assert status.starred_at is not None  # Set automatically when is_starred=True
        assert status.created_at is not None
        assert status.updated_at is not None
    
    def test_read_status_defaults(self, sample_user, sample_article):
        '''Test read status default values'''
        status = ReadStatus.create(
            user=sample_user,
            article=sample_article
        )
        
        assert status.is_read is False  # Default
        assert status.is_starred is False  # Default
        assert status.is_archived is False  # Default
        assert status.read_at is None  # Not set when is_read=False
        assert status.starred_at is None  # Not set when is_starred=False
    
    def test_one_status_per_user_article_pair(self, sample_user, sample_article):
        '''Test that only one status record exists per user-article pair'''
        ReadStatus.create(
            user=sample_user,
            article=sample_article
        )
        
        with pytest.raises(IntegrityError):
            ReadStatus.create(
                user=sample_user,
                article=sample_article
            )
    
    def test_read_status_timestamps_management(self, sample_user, sample_article):
        '''Test automatic timestamp management for read and starred status'''
        status = ReadStatus.create(
            user=sample_user,
            article=sample_article,
            is_read=False,
            is_starred=False
        )
        
        # Initially no timestamps
        assert status.read_at is None
        assert status.starred_at is None
        
        # Mark as read
        status.is_read = True
        status.save()
        assert status.read_at is not None
        
        # Mark as starred
        status.is_starred = True
        status.save()
        assert status.starred_at is not None
        
        # Mark as unread
        status.is_read = False
        status.save()
        assert status.read_at is None  # Cleared
        assert status.starred_at is not None  # Still starred
        
        # Mark as unstarred
        status.is_starred = False
        status.save()
        assert status.starred_at is None  # Cleared
    
    def test_read_status_relationships(self, sample_user, sample_article):
        '''Test read status relationships'''
        status = ReadStatus.create(
            user=sample_user,
            article=sample_article,
            is_read=True
        )
        
        # Test forward relationships
        assert status.user.username == 'reader'
        assert status.article.title == 'Sample Article'
        
        # Test reverse relationships (backrefs)
        user_statuses = list(sample_user.read_statuses)
        assert len(user_statuses) == 1
        assert user_statuses[0] == status
        
        article_statuses = list(sample_article.read_statuses)
        assert len(article_statuses) == 1
        assert article_statuses[0] == status
    
    def test_read_status_string_representation(self, sample_user, sample_article):
        '''Test read status string representation'''
        # Unread status
        status = ReadStatus.create(
            user=sample_user,
            article=sample_article
        )
        assert str(status) == 'reader: Sample Article (unread)'
        
        # Read status
        status.is_read = True
        status.save()
        assert str(status) == 'reader: Sample Article (read)'
        
        # Read and starred
        status.is_starred = True
        status.save()
        assert str(status) == 'reader: Sample Article (read, starred)'
        
        # Read, starred, and archived
        status.is_archived = True
        status.save()
        assert str(status) == 'reader: Sample Article (read, starred, archived)'
    
    def test_get_or_create_for_user_article(self, sample_user, sample_article):
        '''Test getting or creating read status for user-article pair'''
        # First call should create new status
        status1 = ReadStatus.get_or_create_for_user_article(sample_user, sample_article)
        assert status1.user == sample_user
        assert status1.article == sample_article
        assert not status1.is_read  # Default
        
        # Second call should return existing status
        status2 = ReadStatus.get_or_create_for_user_article(sample_user, sample_article)
        assert status1.id == status2.id
    
    def test_mark_read_convenience_method(self, sample_user, sample_article):
        '''Test mark_read convenience method'''
        # Mark as read
        status = ReadStatus.mark_read(sample_user, sample_article, True)
        assert status.is_read is True
        assert status.read_at is not None
        
        # Mark as unread
        status = ReadStatus.mark_read(sample_user, sample_article, False)
        assert status.is_read is False
        assert status.read_at is None
    
    def test_mark_starred_convenience_method(self, sample_user, sample_article):
        '''Test mark_starred convenience method'''
        # Mark as starred
        status = ReadStatus.mark_starred(sample_user, sample_article, True)
        assert status.is_starred is True
        assert status.starred_at is not None
        
        # Mark as unstarred
        status = ReadStatus.mark_starred(sample_user, sample_article, False)
        assert status.is_starred is False
        assert status.starred_at is None


class TestCascadingDeletes:
    '''Test cascading delete behavior'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [Category, Feed, User, Article, UserSubscription, ReadStatus]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    def test_deleting_user_cascades_to_subscriptions_and_read_statuses(self):
        '''Test that deleting a user cascades to related records'''
        # Create test data
        user = User.create(username='testuser', email='test@example.com', password_hash='pass')
        category = Category.create(name='News')
        feed = Feed.create(url='https://example.com/feed.xml', title='Feed', category=category)
        article = Article.create(feed=feed, title='Article', url='https://example.com/1', guid='1')
        
        subscription = UserSubscription.create(user=user, feed=feed)
        read_status = ReadStatus.create(user=user, article=article)
        
        # Verify records exist
        assert UserSubscription.select().count() == 1
        assert ReadStatus.select().count() == 1
        
        # Delete user
        user.delete_instance()
        
        # Verify cascading deletes
        assert UserSubscription.select().count() == 0
        assert ReadStatus.select().count() == 0
    
    def test_deleting_feed_cascades_to_articles_and_subscriptions(self):
        '''Test that deleting a feed cascades to related records'''
        # Create test data
        user = User.create(username='testuser', email='test@example.com', password_hash='pass')
        category = Category.create(name='News')
        feed = Feed.create(url='https://example.com/feed.xml', title='Feed', category=category)
        article = Article.create(feed=feed, title='Article', url='https://example.com/1', guid='1')
        
        subscription = UserSubscription.create(user=user, feed=feed)
        read_status = ReadStatus.create(user=user, article=article)
        
        # Verify records exist
        assert Article.select().count() == 1
        assert UserSubscription.select().count() == 1
        assert ReadStatus.select().count() == 1
        
        # Delete feed
        feed.delete_instance()
        
        # Verify cascading deletes
        assert Article.select().count() == 0  # Articles cascade delete
        assert UserSubscription.select().count() == 0  # Subscriptions cascade delete
        assert ReadStatus.select().count() == 0  # Read statuses cascade delete (via article)
    
    def test_deleting_article_cascades_to_read_statuses(self):
        '''Test that deleting an article cascades to read statuses'''
        # Create test data
        user = User.create(username='testuser', email='test@example.com', password_hash='pass')
        category = Category.create(name='News')
        feed = Feed.create(url='https://example.com/feed.xml', title='Feed', category=category)
        article = Article.create(feed=feed, title='Article', url='https://example.com/1', guid='1')
        
        read_status = ReadStatus.create(user=user, article=article)
        
        # Verify record exists
        assert ReadStatus.select().count() == 1
        
        # Delete article
        article.delete_instance()
        
        # Verify cascading delete
        assert ReadStatus.select().count() == 0