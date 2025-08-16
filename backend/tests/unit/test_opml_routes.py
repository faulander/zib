import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from io import BytesIO
from app.main import app
from app.services.opml import (
    ImportProcessorResult,
    ImportStatus,
    ImportPhase,
    ImportResults
)


client = TestClient(app)


class TestOPMLImportRoutes:
    '''Test OPML import REST API endpoints'''
    
    @pytest.fixture
    def sample_opml_file(self):
        '''Sample OPML file content for testing'''
        content = '''<?xml version="1.0" encoding="UTF-8"?>
        <opml version="1.0">
            <head>
                <title>Test Subscriptions</title>
            </head>
            <body>
                <outline text="Technology">
                    <outline text="TechCrunch" xmlUrl="https://techcrunch.com/feed/" htmlUrl="https://techcrunch.com/"/>
                    <outline text="Hacker News" xmlUrl="https://news.ycombinator.com/rss" htmlUrl="https://news.ycombinator.com/"/>
                </outline>
            </body>
        </opml>'''
        return BytesIO(content.encode('utf-8'))
    
    @pytest.fixture
    def mock_import_result(self):
        '''Mock import processor result'''
        return ImportProcessorResult(
            job_id='imp_test123',
            success=True,
            categories_created=1,
            feeds_imported=2,
            feeds_failed=0,
            duplicates_found=0,
            total_processing_time=120.5
        )
    
    @pytest.fixture
    def mock_job_status(self):
        '''Mock import job status data'''
        return {
            'id': 'imp_test123',
            'user_id': 1,
            'filename': 'subscriptions.opml',
            'file_size': 1024,
            'status': ImportStatus.PROCESSING.value,
            'current_phase': ImportPhase.IMPORTING_FEEDS.value,
            'current_step': 15,
            'total_steps': 20,
            'categories_created': 1,
            'feeds_imported': 10,
            'feeds_failed': 0,
            'duplicates_found': 2,
            'created_at': '2023-12-15T10:30:00Z',
            'started_at': '2023-12-15T10:30:15Z',
            'completed_at': None,
            'error_message': None
        }
    
    def test_import_opml_success(self, sample_opml_file, mock_import_result):
        '''Test successful OPML import via API'''
        with patch('app.routes.opml.import_processor') as mock_processor:
            mock_processor.process_import = AsyncMock(return_value=mock_import_result)
            
            response = client.post(
                '/api/import/opml',
                files={'file': ('subscriptions.opml', sample_opml_file, 'application/xml')},
                data={
                    'duplicate_strategy': 'skip',
                    'validate_feeds': 'true',
                    'merge_categories': 'true'
                },
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == status.HTTP_202_ACCEPTED
            
            data = response.json()
            assert data['job_id'] == 'imp_test123'
            assert data['message'] == 'OPML import started successfully'
            assert data['status'] == 'processing'
            
            # Verify processor was called correctly
            mock_processor.process_import.assert_called_once()
            call_args = mock_processor.process_import.call_args
            assert call_args[1]['filename'] == 'subscriptions.opml'
            assert call_args[1]['options']['duplicate_strategy'] == 'skip'
            assert call_args[1]['options']['validate_feeds'] is True
            assert call_args[1]['options']['merge_categories'] is True
    
    def test_import_opml_no_file(self):
        '''Test OPML import without file'''
        response = client.post(
            '/api/import/opml',
            data={'duplicate_strategy': 'skip'},
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert 'file' in response.json()['detail'][0]['loc']
    
    def test_import_opml_invalid_file_type(self):
        '''Test OPML import with invalid file type'''
        text_file = BytesIO(b'This is not XML')
        
        response = client.post(
            '/api/import/opml',
            files={'file': ('document.txt', text_file, 'text/plain')},
            data={'duplicate_strategy': 'skip'},
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert 'Invalid file type' in data['message']
    
    def test_import_opml_file_too_large(self):
        '''Test OPML import with file too large'''
        # Create a large file (> 5MB)
        large_content = b'<opml>' + b'x' * (6 * 1024 * 1024) + b'</opml>'
        large_file = BytesIO(large_content)
        
        response = client.post(
            '/api/import/opml',
            files={'file': ('large.opml', large_file, 'application/xml')},
            data={'duplicate_strategy': 'skip'},
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        data = response.json()
        assert 'File too large' in data['detail']
    
    def test_import_opml_processing_error(self, sample_opml_file):
        '''Test OPML import with processing error'''
        error_result = ImportProcessorResult(
            job_id='imp_error123',
            success=False,
            categories_created=0,
            feeds_imported=0,
            feeds_failed=0,
            duplicates_found=0,
            total_processing_time=5.0,
            error_message='Failed to parse OPML: Invalid XML format'
        )
        
        with patch('app.routes.opml.import_processor') as mock_processor:
            mock_processor.process_import = AsyncMock(return_value=error_result)
            
            response = client.post(
                '/api/import/opml',
                files={'file': ('subscriptions.opml', sample_opml_file, 'application/xml')},
                data={'duplicate_strategy': 'skip'},
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data['job_id'] == 'imp_error123'
            assert 'Failed to parse OPML' in data['detail']
    
    def test_import_opml_unauthorized(self, sample_opml_file):
        '''Test OPML import without authentication'''
        response = client.post(
            '/api/import/opml',
            files={'file': ('subscriptions.opml', sample_opml_file, 'application/xml')},
            data={'duplicate_strategy': 'skip'}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_import_job_success(self, mock_job_status):
        '''Test getting import job status'''
        with patch('app.routes.opml.import_manager') as mock_manager:
            mock_job = Mock()
            for key, value in mock_job_status.items():
                setattr(mock_job, key, value)
            
            mock_manager.get_job.return_value = mock_job
            
            response = client.get(
                '/api/import/jobs/imp_test123',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data['id'] == 'imp_test123'
            assert data['status'] == ImportStatus.PROCESSING.value
            assert data['current_phase'] == ImportPhase.IMPORTING_FEEDS.value
            assert data['progress_percentage'] == 75.0  # 15/20 * 100
            assert data['categories_created'] == 1
            assert data['feeds_imported'] == 10
    
    def test_get_import_job_not_found(self):
        '''Test getting non-existent import job'''
        with patch('app.routes.opml.import_manager') as mock_manager:
            mock_manager.get_job.return_value = None
            
            response = client.get(
                '/api/import/jobs/nonexistent',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data['detail'] == 'Import job not found'
    
    def test_get_import_job_unauthorized(self):
        '''Test getting import job without authentication'''
        response = client.get('/api/import/jobs/imp_test123')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_import_jobs_success(self):
        '''Test listing import jobs'''
        mock_jobs = [
            Mock(
                id='imp_job1',
                filename='feeds1.opml',
                status=ImportStatus.COMPLETED.value,
                created_at='2023-12-15T10:00:00Z',
                feeds_imported=10,
                categories_created=2
            ),
            Mock(
                id='imp_job2',
                filename='feeds2.opml',
                status=ImportStatus.PROCESSING.value,
                created_at='2023-12-15T11:00:00Z',
                feeds_imported=5,
                categories_created=1
            )
        ]
        
        with patch('app.routes.opml.import_manager') as mock_manager:
            mock_manager.list_jobs.return_value = mock_jobs
            
            response = client.get(
                '/api/import/jobs',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert len(data['jobs']) == 2
            assert data['jobs'][0]['id'] == 'imp_job1'
            assert data['jobs'][0]['status'] == ImportStatus.COMPLETED.value
            assert data['jobs'][1]['id'] == 'imp_job2'
            assert data['jobs'][1]['status'] == ImportStatus.PROCESSING.value
    
    def test_list_import_jobs_with_filters(self):
        '''Test listing import jobs with status filter'''
        mock_jobs = [
            Mock(
                id='imp_job1',
                filename='feeds1.opml',
                status=ImportStatus.COMPLETED.value,
                created_at='2023-12-15T10:00:00Z',
                feeds_imported=10,
                categories_created=2
            )
        ]
        
        with patch('app.routes.opml.import_manager') as mock_manager:
            mock_manager.list_jobs.return_value = mock_jobs
            
            response = client.get(
                '/api/import/jobs?status=completed&limit=10',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert len(data['jobs']) == 1
            assert data['jobs'][0]['status'] == ImportStatus.COMPLETED.value
            
            # Verify filters were applied
            mock_manager.list_jobs.assert_called_once_with(
                user_id=1,  # From auth
                status=ImportStatus.COMPLETED,
                limit=10
            )
    
    def test_list_import_jobs_unauthorized(self):
        '''Test listing import jobs without authentication'''
        response = client.get('/api/import/jobs')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_cancel_import_job_success(self):
        '''Test cancelling an import job'''
        with patch('app.routes.opml.import_manager') as mock_manager:
            mock_manager.cancel_job.return_value = True
            
            response = client.delete(
                '/api/import/jobs/imp_test123',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data['message'] == 'Import job cancelled successfully'
            
            mock_manager.cancel_job.assert_called_once_with('imp_test123')
    
    def test_cancel_import_job_failure(self):
        '''Test cancelling import job that cannot be cancelled'''
        with patch('app.routes.opml.import_manager') as mock_manager:
            mock_manager.cancel_job.return_value = False
            
            response = client.delete(
                '/api/import/jobs/imp_test123',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert 'Cannot cancel import job' in data['detail']
    
    def test_cancel_import_job_unauthorized(self):
        '''Test cancelling import job without authentication'''
        response = client.delete('/api/import/jobs/imp_test123')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_import_opml_with_category_parent(self, sample_opml_file, mock_import_result):
        '''Test OPML import with category parent'''
        with patch('app.routes.opml.import_processor') as mock_processor:
            mock_processor.process_import = AsyncMock(return_value=mock_import_result)
            
            response = client.post(
                '/api/import/opml',
                files={'file': ('subscriptions.opml', sample_opml_file, 'application/xml')},
                data={
                    'duplicate_strategy': 'merge',
                    'validate_feeds': 'false',
                    'merge_categories': 'false',
                    'category_parent_id': '5'
                },
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == status.HTTP_202_ACCEPTED
            
            # Verify options were passed correctly
            call_args = mock_processor.process_import.call_args
            options = call_args[1]['options']
            assert options['duplicate_strategy'] == 'merge'
            assert options['validate_feeds'] is False
            assert options['merge_categories'] is False
            assert options['category_parent_id'] == 5
    
    def test_import_opml_default_options(self, sample_opml_file, mock_import_result):
        '''Test OPML import with default options'''
        with patch('app.routes.opml.import_processor') as mock_processor:
            mock_processor.process_import = AsyncMock(return_value=mock_import_result)
            
            response = client.post(
                '/api/import/opml',
                files={'file': ('subscriptions.opml', sample_opml_file, 'application/xml')},
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == status.HTTP_202_ACCEPTED
            
            # Verify default options
            call_args = mock_processor.process_import.call_args
            options = call_args[1]['options']
            assert options['duplicate_strategy'] == 'skip'  # Default
            assert options['validate_feeds'] is True  # Default
            assert options['merge_categories'] is True  # Default
            assert options['category_parent_id'] is None  # Default