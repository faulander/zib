import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime, timedelta
from app.services.opml.import_manager import (
    ImportJobManager,
    ImportJobError,
    ImportStatus,
    ImportPhase,
    ImportProgress,
    ImportResults
)
from app.models.base import ImportJob


class TestImportJobManager:
    '''Test import job management functionality'''
    
    @pytest.fixture
    def manager(self):
        '''Create an import job manager instance'''
        return ImportJobManager()
    
    @pytest.fixture
    def sample_job_data(self):
        '''Sample job creation data'''
        return {
            'user_id': 123,
            'filename': 'subscriptions.opml',
            'file_size': 1024,
            'duplicate_strategy': 'skip',
            'validate_feeds': True,
            'category_parent_id': None
        }
    
    @pytest.fixture
    def mock_import_job(self):
        '''Mock ImportJob instance'''
        job = Mock(spec=ImportJob)
        job.id = 'imp_test123'
        job.user_id = 123
        job.filename = 'subscriptions.opml'
        job.file_size = 1024
        job.status = ImportStatus.PENDING.value
        job.duplicate_strategy = 'skip'
        job.validate_feeds = True
        job.category_parent = None
        job.total_steps = 0
        job.current_step = 0
        job.current_phase = None
        job.categories_created = 0
        job.feeds_imported = 0
        job.feeds_failed = 0
        job.duplicates_found = 0
        job.created_at = datetime.now()
        job.started_at = None
        job.completed_at = None
        job.error_message = None
        job.error_details = None
        return job
    
    def test_create_job_success(self, manager, sample_job_data):
        '''Test successful job creation'''
        with patch('app.services.opml.import_manager.ImportJob.create') as mock_create:
            mock_job = Mock(spec=ImportJob)
            mock_job.id = 'imp_test123'
            mock_create.return_value = mock_job
            
            job_id = manager.create_job(**sample_job_data)
            
            assert job_id.startswith('imp_')
            assert len(job_id) == 16  # 'imp_' + 12 hex characters
            assert job_id in manager._active_jobs
            assert job_id in manager._progress_callbacks
            assert job_id in manager._status_callbacks
            
            # Verify job creation was called with correct parameters
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['user_id'] == sample_job_data['user_id']
            assert call_args['filename'] == sample_job_data['filename']
            assert call_args['file_size'] == sample_job_data['file_size']
            assert call_args['status'] == ImportStatus.PENDING.value
    
    def test_create_job_failure(self, manager, sample_job_data):
        '''Test job creation failure'''
        with patch('app.services.opml.import_manager.ImportJob.create', 
                   side_effect=Exception('Database error')):
            with pytest.raises(ImportJobError) as exc_info:
                manager.create_job(**sample_job_data)
            
            assert 'Failed to create import job' in str(exc_info.value)
    
    def test_get_job_from_cache(self, manager, mock_import_job):
        '''Test getting job from active cache'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        
        result = manager.get_job(job_id)
        
        assert result == mock_import_job
    
    def test_get_job_from_database(self, manager):
        '''Test getting job from database'''
        job_id = 'imp_test123'
        
        with patch('app.services.opml.import_manager.ImportJob.get_by_id') as mock_get:
            mock_job = Mock(spec=ImportJob)
            mock_job.id = job_id
            mock_get.return_value = mock_job
            
            result = manager.get_job(job_id)
            
            assert result == mock_job
            assert job_id in manager._active_jobs
            mock_get.assert_called_once_with(job_id)
    
    def test_get_job_not_found(self, manager):
        '''Test getting non-existent job'''
        with patch('app.services.opml.import_manager.ImportJob.get_by_id', 
                   side_effect=ImportJob.DoesNotExist):
            result = manager.get_job('nonexistent')
            
            assert result is None
    
    def test_start_job_success(self, manager, mock_import_job):
        '''Test successful job start'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        manager._status_callbacks[job_id] = []
        
        mock_import_job.status = ImportStatus.PENDING.value
        
        success = manager.start_job(job_id, total_steps=10)
        
        assert success is True
        assert mock_import_job.status == ImportStatus.PROCESSING.value
        assert mock_import_job.total_steps == 10
        assert mock_import_job.current_step == 0
        assert mock_import_job.started_at is not None
        mock_import_job.save.assert_called_once()
    
    def test_start_job_not_found(self, manager):
        '''Test starting non-existent job'''
        success = manager.start_job('nonexistent', total_steps=10)
        
        assert success is False
    
    def test_start_job_wrong_status(self, manager, mock_import_job):
        '''Test starting job with wrong status'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        mock_import_job.status = ImportStatus.PROCESSING.value
        
        success = manager.start_job(job_id, total_steps=10)
        
        assert success is False
        # Should not modify the job
        mock_import_job.save.assert_not_called()
    
    def test_update_progress_success(self, manager, mock_import_job):
        '''Test successful progress update'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        manager._progress_callbacks[job_id] = []
        
        mock_import_job.status = ImportStatus.PROCESSING.value
        mock_import_job.total_steps = 10
        
        success = manager.update_progress(job_id, 5, ImportPhase.VALIDATING_FEEDS, 'Validating feeds')
        
        assert success is True
        assert mock_import_job.current_step == 5
        assert mock_import_job.current_phase == ImportPhase.VALIDATING_FEEDS.value
        mock_import_job.save.assert_called_once()
    
    def test_update_progress_with_callback(self, manager, mock_import_job):
        '''Test progress update with callback notification'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        
        # Add progress callback
        callback = Mock()
        manager._progress_callbacks[job_id] = [callback]
        
        mock_import_job.status = ImportStatus.PROCESSING.value
        mock_import_job.total_steps = 10
        
        manager.update_progress(job_id, 3, ImportPhase.CREATING_CATEGORIES, 'Creating categories')
        
        # Verify callback was called
        callback.assert_called_once()
        call_args = callback.call_args[0]
        assert call_args[0] == job_id
        assert isinstance(call_args[1], ImportProgress)
        assert call_args[1].current_step == 3
        assert call_args[1].percentage == 30.0
    
    def test_complete_job_success(self, manager, mock_import_job):
        '''Test successful job completion'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        manager._status_callbacks[job_id] = []
        
        results = ImportResults(
            categories_created=5,
            feeds_imported=25,
            feeds_failed=2,
            duplicates_found=3,
            total_feeds=30,
            total_categories=5,
            duration_seconds=120.5
        )
        
        success = manager.complete_job(job_id, results)
        
        assert success is True
        assert mock_import_job.status == ImportStatus.COMPLETED.value
        assert mock_import_job.categories_created == 5
        assert mock_import_job.feeds_imported == 25
        assert mock_import_job.feeds_failed == 2
        assert mock_import_job.duplicates_found == 3
        assert mock_import_job.completed_at is not None
        mock_import_job.save.assert_called_once()
        
        # Verify job was cleaned up from active tracking
        assert job_id not in manager._active_jobs
    
    def test_fail_job_success(self, manager, mock_import_job):
        '''Test successful job failure'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        manager._status_callbacks[job_id] = []
        
        error_msg = 'Invalid OPML format'
        error_details = 'XML parsing failed at line 42'
        
        success = manager.fail_job(job_id, error_msg, error_details)
        
        assert success is True
        assert mock_import_job.status == ImportStatus.FAILED.value
        assert mock_import_job.error_message == error_msg
        assert mock_import_job.error_details == error_details
        assert mock_import_job.completed_at is not None
        mock_import_job.save.assert_called_once()
        
        # Verify job was cleaned up from active tracking
        assert job_id not in manager._active_jobs
    
    def test_cancel_job_success(self, manager, mock_import_job):
        '''Test successful job cancellation'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        manager._status_callbacks[job_id] = []
        
        mock_import_job.status = ImportStatus.PROCESSING.value
        
        success = manager.cancel_job(job_id)
        
        assert success is True
        assert mock_import_job.status == ImportStatus.CANCELLED.value
        assert mock_import_job.completed_at is not None
        mock_import_job.save.assert_called_once()
        
        # Verify job was cleaned up from active tracking
        assert job_id not in manager._active_jobs
    
    def test_cancel_completed_job(self, manager, mock_import_job):
        '''Test cancelling already completed job'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        
        mock_import_job.status = ImportStatus.COMPLETED.value
        
        success = manager.cancel_job(job_id)
        
        assert success is False
        # Should not modify completed job
        mock_import_job.save.assert_not_called()
    
    def test_get_job_status(self, manager, mock_import_job):
        '''Test getting job status'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        mock_import_job.status = ImportStatus.PROCESSING.value
        
        status = manager.get_job_status(job_id)
        
        assert status == ImportStatus.PROCESSING
    
    def test_get_job_status_not_found(self, manager):
        '''Test getting status of non-existent job'''
        status = manager.get_job_status('nonexistent')
        
        assert status is None
    
    def test_get_job_progress(self, manager, mock_import_job):
        '''Test getting job progress'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        
        mock_import_job.current_step = 7
        mock_import_job.total_steps = 10
        mock_import_job.current_phase = ImportPhase.IMPORTING_FEEDS.value
        
        progress = manager.get_job_progress(job_id)
        
        assert progress is not None
        assert progress.current_step == 7
        assert progress.total_steps == 10
        assert progress.percentage == 70.0
        assert progress.current_phase == ImportPhase.IMPORTING_FEEDS.value
    
    def test_add_progress_callback(self, manager):
        '''Test adding progress callback'''
        job_id = 'test_job'
        callback = Mock()
        
        manager.add_progress_callback(job_id, callback)
        
        assert job_id in manager._progress_callbacks
        assert callback in manager._progress_callbacks[job_id]
    
    def test_add_status_callback(self, manager):
        '''Test adding status callback'''
        job_id = 'test_job'
        callback = Mock()
        
        manager.add_status_callback(job_id, callback)
        
        assert job_id in manager._status_callbacks
        assert callback in manager._status_callbacks[job_id]
    
    def test_list_jobs_no_filter(self, manager):
        '''Test listing all jobs'''
        with patch('app.services.opml.import_manager.ImportJob.select') as mock_select:
            mock_query = Mock()
            mock_query.order_by.return_value.limit.return_value = ['job1', 'job2']
            mock_select.return_value = mock_query
            
            jobs = manager.list_jobs()
            
            assert jobs == ['job1', 'job2']
            mock_query.order_by.assert_called_once()
            mock_query.order_by.return_value.limit.assert_called_once_with(50)
    
    def test_list_jobs_with_filters(self, manager):
        '''Test listing jobs with user and status filters'''
        with patch('app.services.opml.import_manager.ImportJob.select') as mock_select:
            mock_query = Mock()
            mock_query.where.return_value = mock_query
            mock_query.order_by.return_value.limit.return_value = ['filtered_job']
            mock_select.return_value = mock_query
            
            jobs = manager.list_jobs(user_id=123, status=ImportStatus.COMPLETED, limit=25)
            
            assert jobs == ['filtered_job']
            # Should have two where clauses (user_id and status)
            assert mock_query.where.call_count == 2
            mock_query.order_by.return_value.limit.assert_called_once_with(25)
    
    def test_cleanup_old_jobs(self, manager):
        '''Test cleaning up old jobs'''
        with patch('app.services.opml.import_manager.ImportJob.delete') as mock_delete:
            mock_query = Mock()
            mock_query.where.return_value.execute.return_value = 5
            mock_delete.return_value = mock_query
            
            deleted_count = manager.cleanup_old_jobs(days_old=7)
            
            assert deleted_count == 5
            mock_delete.assert_called_once()
            mock_query.where.assert_called_once()
    
    def test_callback_error_handling(self, manager, mock_import_job):
        '''Test error handling in callbacks'''
        job_id = mock_import_job.id
        manager._active_jobs[job_id] = mock_import_job
        
        # Add callback that raises exception
        error_callback = Mock(side_effect=Exception('Callback error'))
        good_callback = Mock()
        
        manager._progress_callbacks[job_id] = [error_callback, good_callback]
        manager._status_callbacks[job_id] = [error_callback, good_callback]
        
        mock_import_job.status = ImportStatus.PROCESSING.value
        mock_import_job.total_steps = 10
        
        # Should not raise exception despite callback error
        manager.update_progress(job_id, 5, ImportPhase.VALIDATING_FEEDS)
        
        # Both callbacks should have been called
        error_callback.assert_called()
        good_callback.assert_called()
    
    def test_cleanup_job_tracking(self, manager):
        '''Test cleanup of job tracking data'''
        job_id = 'test_job'
        manager._active_jobs[job_id] = Mock()
        manager._progress_callbacks[job_id] = [Mock()]
        manager._status_callbacks[job_id] = [Mock()]
        
        manager._cleanup_job(job_id)
        
        assert job_id not in manager._active_jobs
        assert job_id not in manager._progress_callbacks
        assert job_id not in manager._status_callbacks
    
    def test_manager_singleton_behavior(self):
        '''Test that import_manager singleton is available'''
        from app.services.opml.import_manager import import_manager
        
        assert isinstance(import_manager, ImportJobManager)
        
        # Should be the same instance
        from app.services.opml.import_manager import import_manager as manager2
        assert import_manager is manager2