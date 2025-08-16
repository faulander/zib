import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db
from app.models.base import Category, Feed

client = TestClient(app)


class TestCategoryAPICRUD:
    '''Test Category API CRUD operations'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Setup test database and clear data before each test'''
        db.connect(reuse_if_open=True)
        db.drop_tables([Category, Feed], safe=True)
        db.create_tables([Category, Feed])
        yield
        db.drop_tables([Category, Feed], safe=True)
        db.close()
    
    def test_create_category_success(self):
        '''Test successful category creation'''
        category_data = {
            'name': 'Technology',
            'description': 'Tech news and articles',
            'color': '#3B82F6'
        }
        
        response = client.post('/api/categories/', json=category_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'Technology'
        assert data['description'] == 'Tech news and articles'
        assert data['color'] == '#3B82F6'
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_create_category_minimal(self):
        '''Test category creation with minimal data'''
        category_data = {'name': 'Sports'}
        
        response = client.post('/api/categories/', json=category_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'Sports'
        assert data['description'] is None
        assert data['color'] is None
    
    def test_create_category_validation_errors(self):
        '''Test category creation validation errors'''
        # Empty name
        response = client.post('/api/categories/', json={'name': ''})
        assert response.status_code == 422
        
        # Missing name
        response = client.post('/api/categories/', json={'description': 'No name'})
        assert response.status_code == 422
        
        # Invalid color format
        response = client.post('/api/categories/', json={
            'name': 'Tech',
            'color': 'invalid-color'
        })
        assert response.status_code == 422
    
    def test_create_category_duplicate_name(self):
        '''Test duplicate category name error'''
        category_data = {'name': 'Technology'}
        
        # Create first category
        response = client.post('/api/categories/', json=category_data)
        assert response.status_code == 201
        
        # Try to create duplicate
        response = client.post('/api/categories/', json=category_data)
        assert response.status_code == 400
        data = response.json()
        assert 'already exists' in data['message']
    
    def test_get_category_by_id_success(self):
        '''Test successful category retrieval by ID'''
        # Create category first
        category_data = {'name': 'Technology', 'color': '#3B82F6'}
        create_response = client.post('/api/categories/', json=category_data)
        category_id = create_response.json()['id']
        
        # Get category
        response = client.get(f'/api/categories/{category_id}')
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == category_id
        assert data['name'] == 'Technology'
        assert data['color'] == '#3B82F6'
    
    def test_get_category_not_found(self):
        '''Test category not found error'''
        response = client.get('/api/categories/999')
        
        assert response.status_code == 404
        data = response.json()
        assert 'not found' in data['message']
    
    def test_list_categories_empty(self):
        '''Test listing categories when none exist'''
        response = client.get('/api/categories/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['items'] == []
        assert data['total'] == 0
        assert data['page'] == 1
        assert data['pages'] == 1
    
    def test_list_categories_with_data(self):
        '''Test listing categories with data'''
        # Create multiple categories
        categories = [
            {'name': 'Technology', 'color': '#3B82F6'},
            {'name': 'Sports', 'color': '#EF4444'},
            {'name': 'Politics', 'color': '#10B981'}
        ]
        
        for category in categories:
            client.post('/api/categories/', json=category)
        
        # List categories
        response = client.get('/api/categories/')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 3
        assert data['total'] == 3
        assert data['page'] == 1
        assert data['pages'] == 1
        
        # Check category names are present
        names = [item['name'] for item in data['items']]
        assert 'Technology' in names
        assert 'Sports' in names
        assert 'Politics' in names
    
    def test_list_categories_pagination(self):
        '''Test category listing with pagination'''
        # Create 5 categories
        for i in range(5):
            client.post('/api/categories/', json={'name': f'Category {i+1}'})
        
        # Get first page with page size 2
        response = client.get('/api/categories/?page=1&page_size=2')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 2
        assert data['total'] == 5
        assert data['page'] == 1
        assert data['page_size'] == 2
        assert data['pages'] == 3
        
        # Get second page
        response = client.get('/api/categories/?page=2&page_size=2')
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 2
        assert data['page'] == 2
    
    def test_update_category_success(self):
        '''Test successful category update'''
        # Create category
        category_data = {'name': 'Technology', 'description': 'Tech news'}
        create_response = client.post('/api/categories/', json=category_data)
        category_id = create_response.json()['id']
        
        # Update category
        update_data = {
            'name': 'Updated Technology',
            'description': 'Updated tech news',
            'color': '#3B82F6'
        }
        response = client.put(f'/api/categories/{category_id}', json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Updated Technology'
        assert data['description'] == 'Updated tech news'
        assert data['color'] == '#3B82F6'
    
    def test_update_category_partial(self):
        '''Test partial category update'''
        # Create category
        category_data = {'name': 'Technology', 'description': 'Tech news'}
        create_response = client.post('/api/categories/', json=category_data)
        category_id = create_response.json()['id']
        
        # Partial update
        update_data = {'description': 'Updated description only'}
        response = client.put(f'/api/categories/{category_id}', json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Technology'  # Unchanged
        assert data['description'] == 'Updated description only'
    
    def test_update_category_not_found(self):
        '''Test updating non-existent category'''
        update_data = {'name': 'Updated'}
        response = client.put('/api/categories/999', json=update_data)
        
        assert response.status_code == 404
        data = response.json()
        assert 'not found' in data['message']
    
    def test_update_category_duplicate_name(self):
        '''Test updating category with duplicate name'''
        # Create two categories
        client.post('/api/categories/', json={'name': 'Technology'})
        create_response = client.post('/api/categories/', json={'name': 'Sports'})
        category_id = create_response.json()['id']
        
        # Try to update second category with first category's name
        update_data = {'name': 'Technology'}
        response = client.put(f'/api/categories/{category_id}', json=update_data)
        
        assert response.status_code == 400
        data = response.json()
        assert 'already exists' in data['message']
    
    def test_delete_category_success(self):
        '''Test successful category deletion'''
        # Create category
        category_data = {'name': 'Technology'}
        create_response = client.post('/api/categories/', json=category_data)
        category_id = create_response.json()['id']
        
        # Delete category
        response = client.delete(f'/api/categories/{category_id}')
        
        assert response.status_code == 200
        data = response.json()
        assert 'deleted successfully' in data['message']
        assert data['data']['category_id'] == category_id
        
        # Verify category is deleted
        get_response = client.get(f'/api/categories/{category_id}')
        assert get_response.status_code == 404
    
    def test_delete_category_not_found(self):
        '''Test deleting non-existent category'''
        response = client.delete('/api/categories/999')
        
        assert response.status_code == 404
        data = response.json()
        assert 'not found' in data['message']
    
    def test_delete_category_with_feeds_constraint(self):
        '''Test that category with feeds cannot be deleted'''
        # Create category
        category_data = {'name': 'Technology'}
        create_response = client.post('/api/categories/', json=category_data)
        category_id = create_response.json()['id']
        
        # Create feed in this category
        feed_data = {
            'url': 'https://example.com/rss.xml',
            'title': 'Tech Feed',
            'category_id': category_id
        }
        client.post('/api/feeds/', json=feed_data)
        
        # Try to delete category
        response = client.delete(f'/api/categories/{category_id}')
        
        assert response.status_code == 400
        data = response.json()
        assert 'Cannot delete category' in data['message']
        assert 'feeds' in data['message']
    
    def test_get_category_with_feeds(self):
        '''Test getting category with feed count'''
        # Create category
        category_data = {'name': 'Technology'}
        create_response = client.post('/api/categories/', json=category_data)
        category_id = create_response.json()['id']
        
        # Create feeds in this category
        for i in range(3):
            feed_data = {
                'url': f'https://example{i}.com/rss.xml',
                'title': f'Tech Feed {i}',
                'category_id': category_id
            }
            client.post('/api/feeds/', json=feed_data)
        
        # Get category with feeds flag
        response = client.get(f'/api/categories/{category_id}?include_feeds=true')
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == category_id
        assert data['name'] == 'Technology'
        assert 'feeds' in data
        assert len(data['feeds']) == 3


class TestCategoryAPIValidation:
    '''Test Category API validation and edge cases'''
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        '''Setup test database and clear data before each test'''
        db.connect(reuse_if_open=True)
        db.drop_tables([Category, Feed], safe=True)
        db.create_tables([Category, Feed])
        yield
        db.drop_tables([Category, Feed], safe=True)
        db.close()
    
    def test_category_name_length_validation(self):
        '''Test category name length validation'''
        # Name too long (over 100 characters)
        long_name = 'x' * 101
        response = client.post('/api/categories/', json={'name': long_name})
        assert response.status_code == 422
    
    def test_category_color_validation(self):
        '''Test category color format validation'''
        invalid_colors = [
            'not-a-color',
            '#ZZZ',
            'rgb(255,255,255)',
            '#GGGGGG',
            'blue'
        ]
        
        for color in invalid_colors:
            response = client.post('/api/categories/', json={
                'name': 'Test',
                'color': color
            })
            assert response.status_code == 422
    
    def test_pagination_validation(self):
        '''Test pagination parameter validation'''
        # Invalid page number
        response = client.get('/api/categories/?page=0')
        assert response.status_code == 422
        
        # Invalid page size
        response = client.get('/api/categories/?page_size=0')
        assert response.status_code == 422
        
        # Page size too large
        response = client.get('/api/categories/?page_size=1001')
        assert response.status_code == 422
    
    def test_invalid_category_id_types(self):
        '''Test invalid category ID types in URL'''
        invalid_ids = ['abc', '1.5', 'null', '']
        
        for invalid_id in invalid_ids:
            if invalid_id:  # Skip empty string as it would be a different route
                response = client.get(f'/api/categories/{invalid_id}')
                assert response.status_code == 422