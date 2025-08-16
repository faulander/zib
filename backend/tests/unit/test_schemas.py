import pytest
import json
from datetime import datetime
from pydantic import ValidationError
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.feed import FeedCreate, FeedUpdate, FeedResponse
from app.schemas.filter import FilterCreate, FilterUpdate, FilterResponse
from app.schemas.common import ErrorResponse, SuccessResponse, PaginatedResponse


class TestCategorySchemas:
    '''Test Category Pydantic schemas'''
    
    def test_category_create_valid(self):
        '''Test valid category creation'''
        data = {
            'name': 'Technology',
            'description': 'Tech news and articles',
            'color': '#3B82F6'
        }
        category = CategoryCreate(**data)
        
        assert category.name == 'Technology'
        assert category.description == 'Tech news and articles'
        assert category.color == '#3B82F6'
    
    def test_category_create_minimal(self):
        '''Test category creation with minimal required fields'''
        data = {'name': 'Tech'}
        category = CategoryCreate(**data)
        
        assert category.name == 'Tech'
        assert category.description is None
        assert category.color is None
    
    def test_category_create_invalid_name(self):
        '''Test category creation with invalid name'''
        with pytest.raises(ValidationError) as exc:
            CategoryCreate(name='')  # Empty name
        
        assert 'String should have at least 1 character' in str(exc.value)
    
    def test_category_create_invalid_color(self):
        '''Test category creation with invalid color format'''
        with pytest.raises(ValidationError) as exc:
            CategoryCreate(name='Tech', color='invalid-color')
        
        assert 'Invalid hex color format' in str(exc.value)
    
    def test_category_create_long_name(self):
        '''Test category creation with name too long'''
        long_name = 'x' * 101  # Exceeds 100 character limit
        
        with pytest.raises(ValidationError) as exc:
            CategoryCreate(name=long_name)
        
        assert 'String should have at most 100 characters' in str(exc.value)
    
    def test_category_update_partial(self):
        '''Test partial category update'''
        data = {'description': 'Updated description'}
        category = CategoryUpdate(**data)
        
        assert category.name is None
        assert category.description == 'Updated description'
        assert category.color is None
    
    def test_category_response_serialization(self):
        '''Test category response schema'''
        now = datetime.now()
        data = {
            'id': 1,
            'name': 'Technology',
            'description': 'Tech news',
            'color': '#3B82F6',
            'created_at': now,
            'updated_at': now
        }
        category = CategoryResponse(**data)
        
        assert category.id == 1
        assert category.name == 'Technology'
        assert isinstance(category.created_at, datetime)
        assert isinstance(category.updated_at, datetime)


class TestFeedSchemas:
    '''Test Feed Pydantic schemas'''
    
    def test_feed_create_valid(self):
        '''Test valid feed creation'''
        data = {
            'url': 'https://example.com/rss.xml',
            'title': 'Example Feed',
            'description': 'A sample RSS feed',
            'category_id': 1,
            'fetch_interval': 1800
        }
        feed = FeedCreate(**data)
        
        assert feed.url == 'https://example.com/rss.xml'
        assert feed.title == 'Example Feed'
        assert feed.description == 'A sample RSS feed'
        assert feed.category_id == 1
        assert feed.fetch_interval == 1800
    
    def test_feed_create_minimal(self):
        '''Test feed creation with minimal required fields'''
        data = {'url': 'https://example.com/feed.xml'}
        feed = FeedCreate(**data)
        
        assert feed.url == 'https://example.com/feed.xml'
        assert feed.title is None
        assert feed.description is None
        assert feed.category_id is None
        assert feed.fetch_interval == 3600  # Default value
    
    def test_feed_create_invalid_url(self):
        '''Test feed creation with invalid URL'''
        with pytest.raises(ValidationError) as exc:
            FeedCreate(url='invalid-url')
        
        assert 'Invalid URL format' in str(exc.value)
    
    def test_feed_create_invalid_fetch_interval(self):
        '''Test feed creation with invalid fetch interval'''
        with pytest.raises(ValidationError) as exc:
            FeedCreate(url='https://example.com/feed.xml', fetch_interval=0)
        
        assert 'Input should be greater than or equal to 300' in str(exc.value)
    
    def test_feed_create_long_url(self):
        '''Test feed creation with URL too long'''
        long_url = 'https://example.com/' + 'x' * 500  # Exceeds 500 character limit
        
        with pytest.raises(ValidationError) as exc:
            FeedCreate(url=long_url)
        
        assert 'String should have at most 500 characters' in str(exc.value)
    
    def test_feed_update_partial(self):
        '''Test partial feed update'''
        data = {
            'title': 'Updated Title',
            'is_active': False
        }
        feed = FeedUpdate(**data)
        
        assert feed.title == 'Updated Title'
        assert feed.is_active is False
        assert feed.url is None  # Not being updated
    
    def test_feed_response_serialization(self):
        '''Test feed response schema'''
        now = datetime.now()
        data = {
            'id': 1,
            'url': 'https://example.com/rss.xml',
            'title': 'Example Feed',
            'description': 'Sample feed',
            'category_id': 1,
            'is_active': True,
            'fetch_interval': 3600,
            'last_fetched': now,
            'created_at': now,
            'updated_at': now
        }
        feed = FeedResponse(**data)
        
        assert feed.id == 1
        assert feed.url == 'https://example.com/rss.xml'
        assert feed.is_active is True
        assert isinstance(feed.last_fetched, datetime)
    
    def test_feed_response_basic_structure(self):
        '''Test feed response basic structure'''
        now = datetime.now()
        data = {
            'id': 1,
            'url': 'https://example.com/rss.xml',
            'title': 'Example Feed',
            'category_id': 1,
            'is_active': True,
            'fetch_interval': 3600,
            'created_at': now,
            'updated_at': now
        }
        feed = FeedResponse(**data)
        
        assert feed.id == 1
        assert feed.category_id == 1
        assert feed.title == 'Example Feed'


class TestFilterSchemas:
    '''Test Filter Pydantic schemas'''
    
    def test_filter_create_valid(self):
        '''Test valid filter creation'''
        criteria = {'keywords': ['python', 'programming'], 'exclude': ['beginner']}
        data = {
            'name': 'Python Advanced',
            'type': 'keyword',
            'criteria': criteria
        }
        filter_obj = FilterCreate(**data)
        
        assert filter_obj.name == 'Python Advanced'
        assert filter_obj.type == 'keyword'
        assert filter_obj.criteria == criteria
    
    def test_filter_create_invalid_criteria(self):
        '''Test filter creation with invalid criteria'''
        with pytest.raises(ValidationError) as exc:
            FilterCreate(
                name='Test Filter',
                type='keyword',
                criteria='invalid-json'  # Should be dict, not string
            )
        
        assert 'Input should be a valid dictionary' in str(exc.value)
    
    def test_filter_create_empty_name(self):
        '''Test filter creation with empty name'''
        with pytest.raises(ValidationError) as exc:
            FilterCreate(name='', type='keyword', criteria={})
        
        assert 'String should have at least 1 character' in str(exc.value)
    
    def test_filter_update_partial(self):
        '''Test partial filter update'''
        data = {
            'is_active': False,
            'criteria': {'updated': True}
        }
        filter_obj = FilterUpdate(**data)
        
        assert filter_obj.is_active is False
        assert filter_obj.criteria == {'updated': True}
        assert filter_obj.name is None
    
    def test_filter_response_serialization(self):
        '''Test filter response schema'''
        now = datetime.now()
        criteria = {'keywords': ['test']}
        data = {
            'id': 1,
            'name': 'Test Filter',
            'type': 'keyword',
            'criteria': criteria,
            'is_active': True,
            'created_at': now,
            'updated_at': now
        }
        filter_obj = FilterResponse(**data)
        
        assert filter_obj.id == 1
        assert filter_obj.name == 'Test Filter'
        assert filter_obj.criteria == criteria


class TestCommonSchemas:
    '''Test common response schemas'''
    
    def test_error_response(self):
        '''Test error response schema'''
        data = {
            'error': 'Validation failed',
            'message': 'The provided data is invalid',
            'details': {'field': 'url', 'issue': 'Invalid format'}
        }
        error = ErrorResponse(**data)
        
        assert error.error == 'Validation failed'
        assert error.message == 'The provided data is invalid'
        assert error.details['field'] == 'url'
    
    def test_success_response(self):
        '''Test success response schema'''
        data = {
            'message': 'Operation completed successfully',
            'data': {'id': 1, 'name': 'Test'}
        }
        success = SuccessResponse(**data)
        
        assert success.message == 'Operation completed successfully'
        assert success.data['id'] == 1
    
    def test_paginated_response(self):
        '''Test paginated response schema'''
        items = [{'id': 1, 'name': 'Item 1'}, {'id': 2, 'name': 'Item 2'}]
        data = {
            'items': items,
            'total': 25,
            'page': 1,
            'page_size': 10,
            'pages': 3
        }
        paginated = PaginatedResponse(**data)
        
        assert len(paginated.items) == 2
        assert paginated.total == 25
        assert paginated.page == 1
        assert paginated.page_size == 10
        assert paginated.pages == 3
    
    def test_paginated_response_validation(self):
        '''Test paginated response validation'''
        with pytest.raises(ValidationError) as exc:
            PaginatedResponse(
                items=[],
                total=10,
                page=0,  # Invalid: page should be >= 1
                page_size=10,
                pages=1
            )
        
        assert 'Input should be greater than or equal to 1' in str(exc.value)