import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAPIHealth:
    '''Test basic API functionality'''
    
    def test_root_endpoint(self):
        '''Test root endpoint'''
        response = client.get('/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['app_name'] == 'Zib RSS Reader'
        assert 'docs_url' in data
    
    def test_health_endpoint(self):
        '''Test health check endpoint'''
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['app_name'] == 'Zib RSS Reader'
    
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


class TestFeedAPIStructure:
    '''Test Feed API structure and validation without database'''
    
    def test_feed_api_validation_error(self):
        '''Test that feed API returns proper validation errors'''
        # Try to create feed with invalid data
        response = client.post('/api/feeds/', json={'url': 'invalid-url'})
        
        # Should return validation error
        assert response.status_code == 422
        data = response.json()
        assert 'detail' in data  # FastAPI default validation error format
        assert len(data['detail']) > 0
        assert 'Invalid URL format' in str(data['detail'])
    
    def test_feed_list_endpoint_structure(self):
        '''Test feed list endpoint returns proper structure'''
        # This might fail due to database, but we can check the response structure
        response = client.get('/api/feeds/')
        
        # Should return proper structure even if database fails
        # The exception handler should provide consistent format
        data = response.json()
        
        if response.status_code == 200:
            # Success case - check pagination structure
            assert 'items' in data
            assert 'total' in data
            assert 'page' in data
        else:
            # Error case - check error structure
            assert 'error' in data or 'message' in data


class TestCategoryAPIStructure:
    '''Test Category API structure'''
    
    def test_category_api_validation_error(self):
        '''Test that category API returns proper validation errors'''
        # Try to create category with invalid data
        response = client.post('/api/categories/', json={'name': ''})
        
        # Should return validation error
        assert response.status_code == 422
        data = response.json()
        assert 'detail' in data  # FastAPI default validation error format
        assert len(data['detail']) > 0
        assert 'String should have at least 1 character' in str(data['detail'])