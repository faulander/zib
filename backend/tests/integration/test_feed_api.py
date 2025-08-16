import pytest
from fastapi.testclient import TestClient
from peewee import SqliteDatabase
from app.main import app
from app.models.base import Category, Feed, Filter, SchemaVersion
from app.core.database import db


# Test database for isolated testing
test_db = SqliteDatabase(':memory:', pragmas={'foreign_keys': 1})


@pytest.fixture(scope='function')
def client():
    '''Create test client with isolated database'''
    # Bind models to test database
    models = [Category, Feed, Filter, SchemaVersion]
    
    # Store original database references
    original_databases = {}
    for model in models:
        original_databases[model] = model._meta.database
        model._meta.database = test_db
    
    test_db.connect()
    test_db.create_tables(models)
    
    # Override the global database instance
    original_db_obj = db.obj
    db.obj = test_db
    
    client = TestClient(app)
    
    yield client
    
    # Cleanup
    test_db.drop_tables(models)
    test_db.close()
    
    # Restore original database references
    for model in models:
        model._meta.database = original_databases[model]
    
    # Restore global database instance
    db.obj = original_db_obj


@pytest.fixture
def sample_category(client):
    '''Create a sample category for testing'''
    response = client.post('/api/categories', json={
        'name': 'Technology',
        'description': 'Tech news and articles',
        'color': '#3B82F6'
    })
    return response.json()


@pytest.fixture
def sample_feed_data():
    '''Sample feed data for testing'''
    return {
        'url': 'https://example.com/rss.xml',
        'title': 'Example RSS Feed',
        'description': 'A sample RSS feed for testing',
        'fetch_interval': 1800
    }


class TestFeedCRUD:
    '''Test Feed CRUD operations'''
    
    def test_create_feed_valid(self, client, sample_category, sample_feed_data):
        '''Test creating a valid feed'''
        feed_data = {**sample_feed_data, 'category_id': sample_category['id']}
        
        response = client.post('/api/feeds', json=feed_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data['url'] == feed_data['url']
        assert data['title'] == feed_data['title']
        assert data['category_id'] == sample_category['id']
        assert data['is_active'] is True
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_create_feed_minimal(self, client, sample_feed_data):
        '''Test creating feed with minimal required data'''
        minimal_data = {'url': sample_feed_data['url']}
        
        response = client.post('/api/feeds', json=minimal_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data['url'] == minimal_data['url']
        assert data['title'] is None
        assert data['category_id'] is None
        assert data['fetch_interval'] == 3600  # Default value
    
    def test_create_feed_invalid_url(self, client):
        '''Test creating feed with invalid URL'''
        invalid_data = {'url': 'invalid-url'}
        
        response = client.post('/api/feeds', json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data['error'] == 'Validation Error'
        assert 'Invalid URL format' in str(data['details'])
    
    def test_create_feed_duplicate_url(self, client, sample_feed_data):
        '''Test creating feed with duplicate URL'''
        # Create first feed
        client.post('/api/feeds', json=sample_feed_data)
        
        # Try to create duplicate
        response = client.post('/api/feeds', json=sample_feed_data)
        
        assert response.status_code == 400
        data = response.json()
        assert 'already exists' in data['message'].lower()
    
    def test_get_feed_by_id(self, client, sample_feed_data):
        '''Test retrieving feed by ID'''
        # Create feed
        create_response = client.post('/api/feeds', json=sample_feed_data)
        feed_id = create_response.json()['id']
        
        # Get feed
        response = client.get(f'/api/feeds/{feed_id}')
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == feed_id
        assert data['url'] == sample_feed_data['url']
    
    def test_get_feed_not_found(self, client):
        '''Test retrieving non-existent feed'''
        response = client.get('/api/feeds/999')
        
        assert response.status_code == 404
        data = response.json()
        assert 'not found' in data['message'].lower()
    
    def test_update_feed(self, client, sample_feed_data):
        '''Test updating a feed'''
        # Create feed
        create_response = client.post('/api/feeds', json=sample_feed_data)
        feed_id = create_response.json()['id']
        
        # Update feed
        update_data = {
            'title': 'Updated Feed Title',
            'description': 'Updated description',
            'is_active': False
        }
        response = client.put(f'/api/feeds/{feed_id}', json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == update_data['title']
        assert data['description'] == update_data['description']
        assert data['is_active'] is False
        assert data['url'] == sample_feed_data['url']  # Unchanged
    
    def test_update_feed_partial(self, client, sample_feed_data):
        '''Test partial feed update'''
        # Create feed
        create_response = client.post('/api/feeds', json=sample_feed_data)
        feed_id = create_response.json()['id']
        
        # Partial update
        update_data = {'title': 'New Title Only'}
        response = client.put(f'/api/feeds/{feed_id}', json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == update_data['title']
        assert data['description'] == sample_feed_data['description']  # Unchanged
    
    def test_update_feed_not_found(self, client):
        '''Test updating non-existent feed'''
        update_data = {'title': 'New Title'}
        response = client.put('/api/feeds/999', json=update_data)
        
        assert response.status_code == 404
        data = response.json()
        assert 'not found' in data['message'].lower()
    
    def test_delete_feed(self, client, sample_feed_data):
        '''Test deleting a feed'''
        # Create feed
        create_response = client.post('/api/feeds', json=sample_feed_data)
        feed_id = create_response.json()['id']
        
        # Delete feed
        response = client.delete(f'/api/feeds/{feed_id}')
        
        assert response.status_code == 200
        data = response.json()
        assert 'deleted' in data['message'].lower()
        
        # Verify feed is deleted
        get_response = client.get(f'/api/feeds/{feed_id}')
        assert get_response.status_code == 404
    
    def test_delete_feed_not_found(self, client):
        '''Test deleting non-existent feed'''
        response = client.delete('/api/feeds/999')
        
        assert response.status_code == 404
        data = response.json()
        assert 'not found' in data['message'].lower()


class TestFeedListing:
    '''Test Feed listing and pagination'''
    
    def test_list_feeds_empty(self, client):
        '''Test listing feeds when none exist'''
        response = client.get('/api/feeds')
        
        assert response.status_code == 200
        data = response.json()
        assert data['items'] == []
        assert data['total'] == 0
        assert data['page'] == 1
        assert data['page_size'] == 10
        assert data['pages'] == 0
    
    def test_list_feeds_basic(self, client, sample_category):
        '''Test basic feed listing'''
        # Create multiple feeds
        feeds_data = [
            {
                'url': 'https://feed1.example.com/rss.xml',
                'title': 'Feed 1',
                'category_id': sample_category['id']
            },
            {
                'url': 'https://feed2.example.com/rss.xml',
                'title': 'Feed 2',
                'category_id': sample_category['id']
            }
        ]
        
        for feed_data in feeds_data:
            client.post('/api/feeds', json=feed_data)
        
        # List feeds
        response = client.get('/api/feeds')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 2
        assert data['total'] == 2
        assert data['page'] == 1
        assert data['pages'] == 1
    
    def test_list_feeds_pagination(self, client, sample_category):
        '''Test feed listing with pagination'''
        # Create 15 feeds
        for i in range(15):
            client.post('/api/feeds', json={
                'url': f'https://feed{i}.example.com/rss.xml',
                'title': f'Feed {i}',
                'category_id': sample_category['id']
            })
        
        # Test first page
        response = client.get('/api/feeds?page=1&page_size=5')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 5
        assert data['total'] == 15
        assert data['page'] == 1
        assert data['page_size'] == 5
        assert data['pages'] == 3
        
        # Test second page
        response = client.get('/api/feeds?page=2&page_size=5')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 5
        assert data['page'] == 2
    
    def test_list_feeds_invalid_pagination(self, client):
        '''Test invalid pagination parameters'''
        # Invalid page
        response = client.get('/api/feeds?page=0')
        assert response.status_code == 422
        
        # Invalid page size
        response = client.get('/api/feeds?page_size=0')
        assert response.status_code == 422
        
        # Page size too large
        response = client.get('/api/feeds?page_size=1000')
        assert response.status_code == 422


class TestFeedFiltering:
    '''Test Feed filtering capabilities'''
    
    def test_filter_by_category(self, client):
        '''Test filtering feeds by category'''
        # Create categories
        cat1_response = client.post('/api/categories', json={'name': 'Tech'})
        cat2_response = client.post('/api/categories', json={'name': 'News'})
        
        cat1_id = cat1_response.json()['id']
        cat2_id = cat2_response.json()['id']
        
        # Create feeds in different categories
        client.post('/api/feeds', json={
            'url': 'https://tech.example.com/rss.xml',
            'title': 'Tech Feed',
            'category_id': cat1_id
        })
        client.post('/api/feeds', json={
            'url': 'https://news.example.com/rss.xml',
            'title': 'News Feed',
            'category_id': cat2_id
        })
        client.post('/api/feeds', json={
            'url': 'https://general.example.com/rss.xml',
            'title': 'General Feed'
            # No category
        })
        
        # Filter by category 1
        response = client.get(f'/api/feeds?category_id={cat1_id}')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 1
        assert data['items'][0]['title'] == 'Tech Feed'
    
    def test_filter_by_active_status(self, client, sample_category):
        '''Test filtering feeds by active status'''
        # Create active and inactive feeds
        client.post('/api/feeds', json={
            'url': 'https://active.example.com/rss.xml',
            'title': 'Active Feed',
            'category_id': sample_category['id']
        })
        
        feed2_response = client.post('/api/feeds', json={
            'url': 'https://inactive.example.com/rss.xml',
            'title': 'Inactive Feed',
            'category_id': sample_category['id']
        })
        
        # Deactivate second feed
        feed2_id = feed2_response.json()['id']
        client.put(f'/api/feeds/{feed2_id}', json={'is_active': False})
        
        # Filter by active status
        response = client.get('/api/feeds?is_active=true')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 1
        assert data['items'][0]['title'] == 'Active Feed'
        
        # Filter by inactive status
        response = client.get('/api/feeds?is_active=false')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 1
        assert data['items'][0]['title'] == 'Inactive Feed'
    
    def test_combined_filters(self, client):
        '''Test combining multiple filters'''
        # Create category
        cat_response = client.post('/api/categories', json={'name': 'Tech'})
        cat_id = cat_response.json()['id']
        
        # Create feeds with different combinations
        client.post('/api/feeds', json={
            'url': 'https://tech-active.example.com/rss.xml',
            'title': 'Tech Active',
            'category_id': cat_id
        })
        
        feed2_response = client.post('/api/feeds', json={
            'url': 'https://tech-inactive.example.com/rss.xml',
            'title': 'Tech Inactive',
            'category_id': cat_id
        })
        
        # Deactivate second feed
        feed2_id = feed2_response.json()['id']
        client.put(f'/api/feeds/{feed2_id}', json={'is_active': False})
        
        # Filter by category and active status
        response = client.get(f'/api/feeds?category_id={cat_id}&is_active=true')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 1
        assert data['items'][0]['title'] == 'Tech Active'


class TestFeedWithCategory:
    '''Test Feed operations with category relationships'''
    
    def test_feed_with_category_response(self, client, sample_category, sample_feed_data):
        '''Test that feed response includes category information'''
        feed_data = {**sample_feed_data, 'category_id': sample_category['id']}
        
        # Create feed
        create_response = client.post('/api/feeds', json=feed_data)
        feed_id = create_response.json()['id']
        
        # Get feed with category
        response = client.get(f'/api/feeds/{feed_id}?include_category=true')
        
        assert response.status_code == 200
        data = response.json()
        assert data['category'] is not None
        assert data['category']['id'] == sample_category['id']
        assert data['category']['name'] == sample_category['name']
    
    def test_update_feed_category(self, client, sample_feed_data):
        '''Test updating feed category'''
        # Create two categories
        cat1_response = client.post('/api/categories', json={'name': 'Tech'})
        cat2_response = client.post('/api/categories', json={'name': 'News'})
        
        cat1_id = cat1_response.json()['id']
        cat2_id = cat2_response.json()['id']
        
        # Create feed with first category
        feed_data = {**sample_feed_data, 'category_id': cat1_id}
        create_response = client.post('/api/feeds', json=feed_data)
        feed_id = create_response.json()['id']
        
        # Update to second category
        response = client.put(f'/api/feeds/{feed_id}', json={'category_id': cat2_id})
        
        assert response.status_code == 200
        data = response.json()
        assert data['category_id'] == cat2_id
    
    def test_remove_feed_category(self, client, sample_category, sample_feed_data):
        '''Test removing category from feed'''
        feed_data = {**sample_feed_data, 'category_id': sample_category['id']}
        
        # Create feed with category
        create_response = client.post('/api/feeds', json=feed_data)
        feed_id = create_response.json()['id']
        
        # Remove category
        response = client.put(f'/api/feeds/{feed_id}', json={'category_id': None})
        
        assert response.status_code == 200
        data = response.json()
        assert data['category_id'] is None