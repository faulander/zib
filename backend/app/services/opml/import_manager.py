'''Import job management system for OPML import operations'''

import uuid
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from loguru import logger
from app.models.base import ImportJob
from app.core.database import db


class ImportStatus(Enum):
    '''Import job status enumeration'''
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class ImportPhase(Enum):
    '''Import process phases'''
    PARSING = 'parsing'
    CREATING_CATEGORIES = 'creating_categories'
    VALIDATING_FEEDS = 'validating_feeds'
    IMPORTING_FEEDS = 'importing_feeds'
    CLEANUP = 'cleanup'


@dataclass
class ImportProgress:
    '''Progress information for an import job'''
    current_step: int
    total_steps: int
    current_phase: str
    phase_description: str
    percentage: float
    eta_seconds: Optional[int] = None


@dataclass
class ImportResults:
    '''Results summary for completed import job'''
    categories_created: int
    feeds_imported: int
    feeds_failed: int
    duplicates_found: int
    total_feeds: int
    total_categories: int
    duration_seconds: float
    error_message: Optional[str] = None


class ImportJobError(Exception):
    '''Exception raised for import job errors'''
    pass


class ImportJobManager:
    '''Manages OPML import jobs with status tracking and progress reporting'''
    
    def __init__(self):
        '''Initialize import job manager'''
        self._active_jobs: Dict[str, ImportJob] = {}
        self._progress_callbacks: Dict[str, List[Callable[[str, ImportProgress], None]]] = {}
        self._status_callbacks: Dict[str, List[Callable[[str, ImportStatus], None]]] = {}
    
    def create_job(self, user_id: int, filename: str, file_size: int,
                   duplicate_strategy: str = 'skip', validate_feeds: bool = True,
                   category_parent_id: Optional[int] = None) -> str:
        '''
        Create a new import job
        
        Args:
            user_id: ID of the user importing OPML
            filename: Name of the OPML file
            file_size: Size of the file in bytes
            duplicate_strategy: How to handle duplicates ('skip', 'update', 'merge', 'prompt')
            validate_feeds: Whether to validate feed URLs
            category_parent_id: Optional parent category for all imported categories
            
        Returns:
            Job ID string
        '''
        # Generate unique job ID
        job_id = f'imp_{uuid.uuid4().hex[:12]}'
        
        try:
            # Create job record in database
            job = ImportJob.create(
                id=job_id,
                user_id=user_id,
                filename=filename,
                file_size=file_size,
                status=ImportStatus.PENDING.value,
                duplicate_strategy=duplicate_strategy,
                category_parent=category_parent_id,
                validate_feeds=validate_feeds,
                created_at=datetime.now()
            )
            
            # Track active job
            self._active_jobs[job_id] = job
            self._progress_callbacks[job_id] = []
            self._status_callbacks[job_id] = []
            
            logger.info(f'Created import job {job_id} for user {user_id}: {filename}')
            return job_id
            
        except Exception as e:
            raise ImportJobError(f'Failed to create import job: {str(e)}')
    
    def get_job(self, job_id: str) -> Optional[ImportJob]:
        '''
        Get import job by ID
        
        Args:
            job_id: Job ID to retrieve
            
        Returns:
            ImportJob instance or None if not found
        '''
        try:
            if job_id in self._active_jobs:
                return self._active_jobs[job_id]
            
            # Try to load from database
            job = ImportJob.get_by_id(job_id)
            self._active_jobs[job_id] = job
            return job
            
        except ImportJob.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f'Error retrieving job {job_id}: {e}')
            return None
    
    def start_job(self, job_id: str, total_steps: int) -> bool:
        '''
        Start an import job
        
        Args:
            job_id: Job ID to start
            total_steps: Total number of steps in the import process
            
        Returns:
            True if job was started successfully
        '''
        try:
            job = self.get_job(job_id)
            if not job:
                raise ImportJobError(f'Job {job_id} not found')
            
            if job.status != ImportStatus.PENDING.value:
                raise ImportJobError(f'Job {job_id} is not in pending status')
            
            # Update job status
            job.status = ImportStatus.PROCESSING.value
            job.started_at = datetime.now()
            job.total_steps = total_steps
            job.current_step = 0
            job.save()
            
            # Notify status callbacks
            self._notify_status_change(job_id, ImportStatus.PROCESSING)
            
            logger.info(f'Started import job {job_id} with {total_steps} total steps')
            return True
            
        except Exception as e:
            logger.error(f'Failed to start job {job_id}: {e}')
            return False
    
    def update_progress(self, job_id: str, current_step: int, 
                       phase: ImportPhase, phase_description: str = '') -> bool:
        '''
        Update job progress
        
        Args:
            job_id: Job ID to update
            current_step: Current step number
            phase: Current import phase
            phase_description: Description of current activity
            
        Returns:
            True if progress was updated successfully
        '''
        try:
            job = self.get_job(job_id)
            if not job:
                raise ImportJobError(f'Job {job_id} not found')
            
            if job.status != ImportStatus.PROCESSING.value:
                logger.warning(f'Attempting to update progress for non-processing job {job_id}')
                return False
            
            # Update job progress
            job.current_step = current_step
            job.current_phase = phase.value
            job.save()
            
            # Calculate progress information
            percentage = (current_step / job.total_steps * 100) if job.total_steps > 0 else 0
            
            progress = ImportProgress(
                current_step=current_step,
                total_steps=job.total_steps,
                current_phase=phase.value,
                phase_description=phase_description,
                percentage=percentage
            )
            
            # Notify progress callbacks
            self._notify_progress_update(job_id, progress)
            
            logger.debug(f'Updated progress for job {job_id}: {current_step}/{job.total_steps} ({percentage:.1f}%)')
            return True
            
        except Exception as e:
            logger.error(f'Failed to update progress for job {job_id}: {e}')
            return False
    
    def complete_job(self, job_id: str, results: ImportResults) -> bool:
        '''
        Mark job as completed
        
        Args:
            job_id: Job ID to complete
            results: Import results summary
            
        Returns:
            True if job was completed successfully
        '''
        try:
            job = self.get_job(job_id)
            if not job:
                raise ImportJobError(f'Job {job_id} not found')
            
            # Update job with results
            job.status = ImportStatus.COMPLETED.value
            job.completed_at = datetime.now()
            job.categories_created = results.categories_created
            job.feeds_imported = results.feeds_imported
            job.feeds_failed = results.feeds_failed
            job.duplicates_found = results.duplicates_found
            job.save()
            
            # Clean up active job tracking
            self._cleanup_job(job_id)
            
            # Notify status callbacks
            self._notify_status_change(job_id, ImportStatus.COMPLETED)
            
            logger.info(f'Completed import job {job_id}: {results.feeds_imported} feeds imported, '
                       f'{results.categories_created} categories created')
            return True
            
        except Exception as e:
            logger.error(f'Failed to complete job {job_id}: {e}')
            return False
    
    def fail_job(self, job_id: str, error_message: str, error_details: Optional[str] = None) -> bool:
        '''
        Mark job as failed
        
        Args:
            job_id: Job ID to fail
            error_message: Error message
            error_details: Optional detailed error information
            
        Returns:
            True if job was marked as failed successfully
        '''
        try:
            job = self.get_job(job_id)
            if not job:
                raise ImportJobError(f'Job {job_id} not found')
            
            # Update job with error information
            job.status = ImportStatus.FAILED.value
            job.completed_at = datetime.now()
            job.error_message = error_message
            job.error_details = error_details
            job.save()
            
            # Clean up active job tracking
            self._cleanup_job(job_id)
            
            # Notify status callbacks
            self._notify_status_change(job_id, ImportStatus.FAILED)
            
            logger.error(f'Failed import job {job_id}: {error_message}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to mark job {job_id} as failed: {e}')
            return False
    
    def cancel_job(self, job_id: str) -> bool:
        '''
        Cancel an import job
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if job was cancelled successfully
        '''
        try:
            job = self.get_job(job_id)
            if not job:
                raise ImportJobError(f'Job {job_id} not found')
            
            if job.status not in [ImportStatus.PENDING.value, ImportStatus.PROCESSING.value]:
                logger.warning(f'Cannot cancel job {job_id} with status {job.status}')
                return False
            
            # Update job status
            job.status = ImportStatus.CANCELLED.value
            job.completed_at = datetime.now()
            job.save()
            
            # Clean up active job tracking
            self._cleanup_job(job_id)
            
            # Notify status callbacks
            self._notify_status_change(job_id, ImportStatus.CANCELLED)
            
            logger.info(f'Cancelled import job {job_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to cancel job {job_id}: {e}')
            return False
    
    def get_job_status(self, job_id: str) -> Optional[ImportStatus]:
        '''
        Get current status of a job
        
        Args:
            job_id: Job ID to check
            
        Returns:
            ImportStatus or None if job not found
        '''
        job = self.get_job(job_id)
        if job:
            return ImportStatus(job.status)
        return None
    
    def get_job_progress(self, job_id: str) -> Optional[ImportProgress]:
        '''
        Get current progress of a job
        
        Args:
            job_id: Job ID to check
            
        Returns:
            ImportProgress or None if job not found
        '''
        job = self.get_job(job_id)
        if not job:
            return None
        
        percentage = (job.current_step / job.total_steps * 100) if job.total_steps > 0 else 0
        
        return ImportProgress(
            current_step=job.current_step,
            total_steps=job.total_steps,
            current_phase=job.current_phase or ImportPhase.PARSING.value,
            phase_description=f'Step {job.current_step} of {job.total_steps}',
            percentage=percentage
        )
    
    def add_progress_callback(self, job_id: str, callback: Callable[[str, ImportProgress], None]):
        '''
        Add progress update callback for a job
        
        Args:
            job_id: Job ID to monitor
            callback: Function to call with progress updates
        '''
        if job_id not in self._progress_callbacks:
            self._progress_callbacks[job_id] = []
        self._progress_callbacks[job_id].append(callback)
    
    def add_status_callback(self, job_id: str, callback: Callable[[str, ImportStatus], None]):
        '''
        Add status change callback for a job
        
        Args:
            job_id: Job ID to monitor
            callback: Function to call with status changes
        '''
        if job_id not in self._status_callbacks:
            self._status_callbacks[job_id] = []
        self._status_callbacks[job_id].append(callback)
    
    def list_jobs(self, user_id: Optional[int] = None, status: Optional[ImportStatus] = None,
                  limit: int = 50) -> List[ImportJob]:
        '''
        List import jobs with optional filtering
        
        Args:
            user_id: Optional user ID filter
            status: Optional status filter
            limit: Maximum number of jobs to return
            
        Returns:
            List of ImportJob instances
        '''
        try:
            query = ImportJob.select()
            
            if user_id is not None:
                query = query.where(ImportJob.user_id == user_id)
            
            if status is not None:
                query = query.where(ImportJob.status == status.value)
            
            query = query.order_by(ImportJob.created_at.desc()).limit(limit)
            
            return list(query)
            
        except Exception as e:
            logger.error(f'Failed to list jobs: {e}')
            return []
    
    def cleanup_old_jobs(self, days_old: int = 30) -> int:
        '''
        Clean up old completed/failed jobs
        
        Args:
            days_old: Delete jobs older than this many days
            
        Returns:
            Number of jobs cleaned up
        '''
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            deleted = ImportJob.delete().where(
                ImportJob.completed_at < cutoff_date,
                ImportJob.status.in_([
                    ImportStatus.COMPLETED.value,
                    ImportStatus.FAILED.value,
                    ImportStatus.CANCELLED.value
                ])
            ).execute()
            
            logger.info(f'Cleaned up {deleted} old import jobs')
            return deleted
            
        except Exception as e:
            logger.error(f'Failed to clean up old jobs: {e}')
            return 0
    
    def _notify_progress_update(self, job_id: str, progress: ImportProgress):
        '''Notify all progress callbacks for a job'''
        callbacks = self._progress_callbacks.get(job_id, [])
        for callback in callbacks:
            try:
                callback(job_id, progress)
            except Exception as e:
                logger.error(f'Progress callback error for job {job_id}: {e}')
    
    def _notify_status_change(self, job_id: str, status: ImportStatus):
        '''Notify all status callbacks for a job'''
        callbacks = self._status_callbacks.get(job_id, [])
        for callback in callbacks:
            try:
                callback(job_id, status)
            except Exception as e:
                logger.error(f'Status callback error for job {job_id}: {e}')
    
    def _cleanup_job(self, job_id: str):
        '''Clean up job tracking for completed/failed/cancelled jobs'''
        self._active_jobs.pop(job_id, None)
        self._progress_callbacks.pop(job_id, None)
        self._status_callbacks.pop(job_id, None)


# Global import job manager instance
import_manager = ImportJobManager()