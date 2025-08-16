import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db
from app.models.base import Category, Feed

client = TestClient(app)


class TestSystemHealth:
    '''Test system health monitoring and endpoints'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Setup test database and clear data before each test'''
        db.connect(reuse_if_open=True)
        db.drop_tables([Category, Feed], safe=True)
        db.create_tables([Category, Feed])
        yield
        db.drop_tables([Category, Feed], safe=True)
        db.close()
    
    def test_root_endpoint(self):
        '''Test root endpoint returns app information'''
        response = client.get('/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['app_name'] == 'Zib RSS Reader'
        assert 'version' in data
        assert 'description' in data
        assert data['docs_url'] == '/docs'
        assert data['health_url'] == '/health'
    
    def test_health_endpoint_basic(self):
        '''Test basic health check endpoint'''
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['app_name'] == 'Zib RSS Reader'
        assert 'version' in data
        assert 'debug' in data
    
    def test_health_endpoint_with_database_check(self):
        '''Test health check with database connectivity verification'''
        response = client.get('/health?check_db=true')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'database' in data
        assert data['database']['status'] == 'connected'
        assert 'connection_time_ms' in data['database']
    
    def test_api_docs_available(self):
        '''Test that API documentation is available'''
        response = client.get('/docs')
        assert response.status_code == 200
        
        response = client.get('/openapi.json')
        assert response.status_code == 200
        
        openapi_data = response.json()
        assert 'paths' in openapi_data
        assert '/api/feeds/' in openapi_data['paths']
        assert '/api/categories/' in openapi_data['paths']
        assert '/health' in openapi_data['paths']


class TestDatabaseConnectivity:
    '''Test database connectivity and health'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Setup test database and clear data before each test'''
        db.connect(reuse_if_open=True)
        db.drop_tables([Category, Feed], safe=True)
        db.create_tables([Category, Feed])
        yield
        db.drop_tables([Category, Feed], safe=True)
        db.close()
    
    def test_database_write_and_read(self):
        '''Test database write and read operations work'''
        # Create a category
        response = client.post('/api/categories/', json={'name': 'Test Category'})
        assert response.status_code == 201
        category_id = response.json()['id']
        
        # Read it back
        response = client.get(f'/api/categories/{category_id}')
        assert response.status_code == 200
        assert response.json()['name'] == 'Test Category'
        
        # Create a feed
        response = client.post('/api/feeds/', json={
            'url': 'https://example.com/rss.xml',
            'title': 'Test Feed',
            'category_id': category_id
        })
        assert response.status_code == 201
        feed_id = response.json()['id']
        
        # Read it back
        response = client.get(f'/api/feeds/{feed_id}')
        assert response.status_code == 200
        assert response.json()['title'] == 'Test Feed'
    
    def test_database_constraints_work(self):
        '''Test that database constraints are enforced'''
        # Test unique constraint on category names
        client.post('/api/categories/', json={'name': 'Unique Category'})
        response = client.post('/api/categories/', json={'name': 'Unique Category'})
        assert response.status_code == 400
        
        # Test foreign key constraint on feeds
        response = client.post('/api/feeds/', json={
            'url': 'https://example.com/rss.xml',
            'category_id': 9999  # Non-existent category
        })
        assert response.status_code == 404  # Feed service validates category exists first
    
    def test_database_transactions_work(self):
        '''Test that database transactions work properly'''
        # This test verifies that partial operations don't leave the database in inconsistent state
        # If a feed creation fails, it shouldn't leave orphaned data
        
        # Create category first
        response = client.post('/api/categories/', json={'name': 'Transaction Test'})
        assert response.status_code == 201
        category_id = response.json()['id']
        
        # Try to create feed with invalid data (this should fail)
        response = client.post('/api/feeds/', json={
            'url': 'invalid-url',  # Invalid URL format
            'category_id': category_id
        })
        assert response.status_code == 422
        
        # Verify category still exists and is clean
        response = client.get(f'/api/categories/{category_id}?include_feeds=true')
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Transaction Test'
        assert len(data.get('feeds', [])) == 0  # No feeds should be associated


class TestAPIIntegration:
    '''Test complete API integration and workflows'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Setup test database and clear data before each test'''
        db.connect(reuse_if_open=True)
        db.drop_tables([Category, Feed], safe=True)
        db.create_tables([Category, Feed])
        yield
        db.drop_tables([Category, Feed], safe=True)
        db.close()
    
    def test_complete_feed_management_workflow(self):
        '''Test complete workflow: create category, add feeds, manage them'''
        # 1. Create categories
        tech_response = client.post('/api/categories/', json={
            'name': 'Technology',
            'description': 'Tech news and articles',
            'color': '#3B82F6'
        })
        assert tech_response.status_code == 201
        tech_id = tech_response.json()['id']
        
        news_response = client.post('/api/categories/', json={
            'name': 'News',
            'description': 'General news',
            'color': '#EF4444'
        })
        assert news_response.status_code == 201
        news_id = news_response.json()['id']
        
        # 2. Add feeds to categories
        feeds_data = [
            {'url': 'https://techcrunch.com/feed/', 'title': 'TechCrunch', 'category_id': tech_id},
            {'url': 'https://hn.algolia.com/api/v1/search_by_date?tags=front_page', 'title': 'Hacker News', 'category_id': tech_id},
            {'url': 'https://rss.cnn.com/rss/edition.rss', 'title': 'CNN', 'category_id': news_id}
        ]
        
        feed_ids = []
        for feed_data in feeds_data:
            response = client.post('/api/feeds/', json=feed_data)
            assert response.status_code == 201
            feed_ids.append(response.json()['id'])
        
        # 3. List all feeds with pagination
        response = client.get('/api/feeds/?page=1&page_size=2')
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 2
        assert data['total'] == 3
        assert data['pages'] == 2
        
        # 4. Filter feeds by category
        response = client.get(f'/api/feeds/?category_id={tech_id}')
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 2  # TechCrunch and Hacker News
        
        # 5. Update feed status
        response = client.put(f'/api/feeds/{feed_ids[0]}', json={'is_active': False})
        assert response.status_code == 200
        
        # 6. List only active feeds
        response = client.get('/api/feeds/?is_active=true')
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 2  # Only active feeds
        
        # 7. Get category with feeds
        response = client.get(f'/api/categories/{tech_id}?include_feeds=true')
        assert response.status_code == 200
        data = response.json()
        assert len(data['feeds']) == 2
        
        # 8. Try to delete category with feeds (should fail)
        response = client.delete(f'/api/categories/{tech_id}')
        assert response.status_code == 400
        
        # 9. Delete feeds first, then category
        for feed_id in feed_ids[:2]:  # Delete tech feeds
            response = client.delete(f'/api/feeds/{feed_id}')
            assert response.status_code == 200
        
        # Now category deletion should work
        response = client.delete(f'/api/categories/{tech_id}')
        assert response.status_code == 200
    
    def test_error_handling_consistency(self):
        '''Test that error responses are consistent across endpoints'''
        # Test 404 errors have consistent format
        endpoints_404 = [
            '/api/categories/999',
            '/api/feeds/999'
        ]
        
        for endpoint in endpoints_404:
            response = client.get(endpoint)
            assert response.status_code == 404
            data = response.json()
            assert 'error' in data
            assert 'message' in data
            assert 'not found' in data['message'].lower()
        
        # Test 422 validation errors have consistent format
        validation_tests = [
            ('/api/categories/', {'name': ''}),  # Empty name
            ('/api/feeds/', {'url': 'invalid-url'}),  # Invalid URL
        ]
        
        for endpoint, invalid_data in validation_tests:
            response = client.post(endpoint, json=invalid_data)
            assert response.status_code == 422
            data = response.json()
            assert 'detail' in data  # FastAPI validation error format
    
    def test_api_performance_baseline(self):
        '''Test basic API performance benchmarks'''
        import time
        
        # Create some test data
        response = client.post('/api/categories/', json={'name': 'Performance Test'})
        category_id = response.json()['id']
        
        # Test response times for common operations
        operations = [
            ('GET', '/health'),
            ('GET', '/api/categories/'),
            ('GET', f'/api/categories/{category_id}'),
            ('POST', '/api/feeds/', {'url': 'https://example.com/feed.xml', 'category_id': category_id})
        ]
        
        for method, endpoint, *data in operations:
            start = time.time()
            if method == 'GET':
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=data[0] if data else {})
            end = time.time()
            
            # Basic performance check - all operations should complete within reasonable time
            assert (end - start) < 1.0, f'{method} {endpoint} took too long: {end - start:.3f}s'
            assert response.status_code in [200, 201], f'{method} {endpoint} failed with {response.status_code}'