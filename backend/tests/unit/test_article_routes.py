import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, timedelta
from app.main import app
from app.models.base import Category, Feed
from app.models.article import Article, User, ReadStatus, UserSubscription
from app.core.database import db


client = TestClient(app)


class TestArticleRoutes:
    '''Test article API endpoints'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [Category, Feed, User, Article, UserSubscription, ReadStatus]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    @pytest.fixture
    def sample_user(self):
        '''Create a sample user'''
        return User.create(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password'
        )
    
    @pytest.fixture
    def sample_category(self):
        '''Create a sample category'''
        return Category.create(
            name='Technology',
            description='Tech articles'
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
    def sample_articles(self, sample_feed):
        '''Create sample articles'''
        articles = []
        
        # Create articles with different dates and statuses
        for i in range(5):
            article = Article.create(
                feed=sample_feed,
                title=f'Article {i + 1}',
                content=f'<p>Content for article {i + 1}</p>',
                url=f'https://example.com/article-{i + 1}',
                guid=f'article-{i + 1}-guid',
                published_date=datetime.now() - timedelta(days=i),
                author=f'Author {i + 1}',
                tags=f'tag{i},technology' if i % 2 == 0 else 'programming,tutorial'
            )
            articles.append(article)
        
        return articles
    
    def test_get_articles_success(self, sample_articles):
        '''Test getting articles list'''
        response = client.get(
            '/api/articles',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert 'articles' in data
        assert 'pagination' in data
        assert len(data['articles']) == 5
        
        # Check article structure
        article = data['articles'][0]
        assert 'id' in article
        assert 'title' in article
        assert 'content' in article
        assert 'url' in article
        assert 'published_date' in article
        assert 'author' in article
        assert 'tags' in article
        assert 'feed' in article
        assert 'read_status' in article
    
    def test_get_articles_with_pagination(self, sample_articles):
        '''Test getting articles with pagination'''
        response = client.get(
            '/api/articles?page=1&per_page=2',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data['articles']) == 2
        
        pagination = data['pagination']
        assert pagination['page'] == 1
        assert pagination['per_page'] == 2
        assert pagination['total'] == 5
        assert pagination['pages'] == 3
        assert pagination['has_next'] is True
        assert pagination['has_prev'] is False
    
    def test_get_articles_filtered_by_feed(self, sample_articles, sample_feed):
        '''Test getting articles filtered by feed'''
        response = client.get(
            f'/api/articles?feed_id={sample_feed.id}',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data['articles']) == 5
        
        # All articles should be from the specified feed
        for article in data['articles']:
            assert article['feed']['id'] == sample_feed.id
    
    def test_get_articles_filtered_by_category(self, sample_articles, sample_category):
        '''Test getting articles filtered by category'''
        response = client.get(
            f'/api/articles?category_id={sample_category.id}',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data['articles']) == 5
        
        # All articles should be from feeds in the specified category
        for article in data['articles']:
            assert article['feed']['category']['id'] == sample_category.id
    
    def test_get_articles_filtered_by_read_status(self, sample_articles, sample_user):
        '''Test getting articles filtered by read status'''
        # Mark some articles as read
        ReadStatus.mark_read(sample_user, sample_articles[0], True)
        ReadStatus.mark_read(sample_user, sample_articles[1], True)
        
        # Get unread articles
        response = client.get(
            '/api/articles?read_status=unread',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data['articles']) == 3  # 3 unread articles
        
        # Get read articles
        response = client.get(
            '/api/articles?read_status=read',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data['articles']) == 2  # 2 read articles
    
    def test_get_articles_search(self, sample_articles):
        '''Test searching articles'''
        response = client.get(
            '/api/articles?search=Article 1',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data['articles']) == 1
        assert 'Article 1' in data['articles'][0]['title']
    
    def test_get_articles_by_tags(self, sample_articles):
        '''Test getting articles by tags'''
        response = client.get(
            '/api/articles?tags=technology',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Should get articles with 'technology' tag
        assert len(data['articles']) >= 1
        
        for article in data['articles']:
            assert 'technology' in article['tags']
    
    def test_get_articles_sorted(self, sample_articles):
        '''Test getting articles with different sorting'''
        # Sort by published date descending (newest first)
        response = client.get(
            '/api/articles?sort=published_date&order=desc',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        articles = data['articles']
        
        # Check that articles are sorted by published date descending
        for i in range(len(articles) - 1):
            current_date = datetime.fromisoformat(articles[i]['published_date'].replace('Z', '+00:00'))
            next_date = datetime.fromisoformat(articles[i + 1]['published_date'].replace('Z', '+00:00'))
            assert current_date >= next_date
    
    def test_get_articles_unauthorized(self, sample_articles):
        '''Test getting articles without authentication'''
        response = client.get('/api/articles')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_article_by_id_success(self, sample_articles):
        '''Test getting a specific article by ID'''
        article = sample_articles[0]
        
        response = client.get(
            f'/api/articles/{article.id}',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['id'] == article.id
        assert data['title'] == article.title
        assert data['content'] == article.content
        assert data['url'] == article.url
        assert 'feed' in data
        assert 'read_status' in data
    
    def test_get_article_by_id_not_found(self):
        '''Test getting non-existent article'''
        response = client.get(
            '/api/articles/99999',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert data['detail'] == 'Article not found'
    
    def test_mark_article_read(self, sample_articles, sample_user):
        '''Test marking an article as read'''
        article = sample_articles[0]
        
        response = client.post(
            f'/api/articles/{article.id}/mark-read',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['message'] == 'Article marked as read'
        
        # Verify read status was created
        read_status = ReadStatus.get(
            (ReadStatus.user == sample_user) & (ReadStatus.article == article)
        )
        assert read_status.is_read is True
        assert read_status.read_at is not None
    
    def test_mark_article_unread(self, sample_articles, sample_user):
        '''Test marking an article as unread'''
        article = sample_articles[0]
        
        # First mark as read
        ReadStatus.mark_read(sample_user, article, True)
        
        response = client.post(
            f'/api/articles/{article.id}/mark-unread',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['message'] == 'Article marked as unread'
        
        # Verify read status was updated
        read_status = ReadStatus.get(
            (ReadStatus.user == sample_user) & (ReadStatus.article == article)
        )
        assert read_status.is_read is False
        assert read_status.read_at is None
    
    def test_star_article(self, sample_articles, sample_user):
        '''Test starring an article'''
        article = sample_articles[0]
        
        response = client.post(
            f'/api/articles/{article.id}/star',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['message'] == 'Article starred'
        
        # Verify starred status
        read_status = ReadStatus.get_or_create_for_user_article(sample_user, article)
        assert read_status.is_starred is True
        assert read_status.starred_at is not None
    
    def test_unstar_article(self, sample_articles, sample_user):
        '''Test unstarring an article'''
        article = sample_articles[0]
        
        # First star the article
        ReadStatus.mark_starred(sample_user, article, True)
        
        response = client.post(
            f'/api/articles/{article.id}/unstar',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['message'] == 'Article unstarred'
        
        # Verify starred status was updated
        read_status = ReadStatus.get(
            (ReadStatus.user == sample_user) & (ReadStatus.article == article)
        )
        assert read_status.is_starred is False
        assert read_status.starred_at is None
    
    def test_bulk_mark_read(self, sample_articles, sample_user):
        '''Test bulk marking articles as read'''
        article_ids = [article.id for article in sample_articles[:3]]
        
        response = client.post(
            '/api/articles/bulk/mark-read',
            json={'article_ids': article_ids},
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['message'] == f'Marked {len(article_ids)} articles as read'
        assert data['updated_count'] == len(article_ids)
        
        # Verify all articles were marked as read
        for article_id in article_ids:
            article = Article.get_by_id(article_id)
            read_status = ReadStatus.get_or_create_for_user_article(sample_user, article)
            assert read_status.is_read is True
    
    def test_bulk_mark_read_by_feed(self, sample_articles, sample_feed, sample_user):
        '''Test bulk marking articles as read by feed'''
        response = client.post(
            f'/api/articles/bulk/mark-read-by-feed/{sample_feed.id}',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['message'] == f'Marked all articles in feed as read'
        assert data['updated_count'] == 5  # All articles in the feed
        
        # Verify all articles in feed were marked as read
        for article in sample_articles:
            read_status = ReadStatus.get_or_create_for_user_article(sample_user, article)
            assert read_status.is_read is True
    
    def test_get_articles_statistics(self, sample_articles, sample_user):
        '''Test getting article statistics'''
        # Mark some articles as read and starred
        ReadStatus.mark_read(sample_user, sample_articles[0], True)
        ReadStatus.mark_read(sample_user, sample_articles[1], True)
        ReadStatus.mark_starred(sample_user, sample_articles[0], True)
        
        response = client.get(
            '/api/articles/stats',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert 'total_articles' in data
        assert 'read_articles' in data
        assert 'unread_articles' in data
        assert 'starred_articles' in data
        
        assert data['total_articles'] == 5
        assert data['read_articles'] == 2
        assert data['unread_articles'] == 3
        assert data['starred_articles'] == 1


class TestArticleValidation:
    '''Test article API validation'''
    
    def test_get_articles_invalid_pagination(self):
        '''Test getting articles with invalid pagination parameters'''
        response = client.get(
            '/api/articles?page=0&per_page=-1',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_articles_invalid_sort_field(self):
        '''Test getting articles with invalid sort field'''
        response = client.get(
            '/api/articles?sort=invalid_field',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_articles_invalid_read_status(self):
        '''Test getting articles with invalid read status filter'''
        response = client.get(
            '/api/articles?read_status=invalid_status',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_bulk_mark_read_empty_list(self):
        '''Test bulk marking with empty article list'''
        response = client.post(
            '/api/articles/bulk/mark-read',
            json={'article_ids': []},
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_bulk_mark_read_invalid_ids(self):
        '''Test bulk marking with invalid article IDs'''
        response = client.post(
            '/api/articles/bulk/mark-read',
            json={'article_ids': [99999, 99998]},
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestArticlePermissions:
    '''Test article API permissions and security'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Set up test database'''
        models = [Category, Feed, User, Article, UserSubscription, ReadStatus]
        db.create_tables(models, safe=True)
        yield
        db.drop_tables(models, safe=True)
    
    def test_user_can_only_see_subscribed_feeds(self):
        '''Test that users can only see articles from feeds they're subscribed to'''
        # This test would be relevant if we implement user-specific feed subscriptions
        # For now, we'll assume users can see all articles
        pass
    
    def test_read_status_is_user_specific(self):
        '''Test that read status is specific to each user'''
        # Create two users
        user1 = User.create(username='user1', email='user1@example.com', password_hash='hash1')
        user2 = User.create(username='user2', email='user2@example.com', password_hash='hash2')
        
        # Create article
        category = Category.create(name='Tech')
        feed = Feed.create(url='https://example.com/feed.xml', title='Feed', category=category)
        article = Article.create(
            feed=feed,
            title='Test Article',
            url='https://example.com/article',
            guid='test-guid'
        )
        
        # User1 marks article as read
        ReadStatus.mark_read(user1, article, True)
        
        # Check that user2's read status is not affected
        user2_status = ReadStatus.get_or_create_for_user_article(user2, article)
        assert user2_status.is_read is False