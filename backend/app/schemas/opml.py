'''Pydantic schemas for OPML import API'''

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ImportJobCreateResponse(BaseModel):
    '''Response for OPML import creation'''
    job_id: str = Field(..., description='Unique identifier for the import job')
    message: str = Field(..., description='Success message')
    status: str = Field(..., description='Initial job status')
    
    class Config:
        schema_extra = {
            'example': {
                'job_id': 'imp_abc123def456',
                'message': 'OPML import started successfully',
                'status': 'processing'
            }
        }


class ImportJobResponse(BaseModel):
    '''Basic import job information for listings'''
    id: str = Field(..., description='Job identifier')
    filename: str = Field(..., description='Original filename')
    status: str = Field(..., description='Current job status')
    current_phase: Optional[str] = Field(None, description='Current processing phase')
    progress_percentage: float = Field(..., description='Progress percentage (0-100)')
    categories_created: int = Field(0, description='Number of categories created')
    feeds_imported: int = Field(0, description='Number of feeds imported')
    feeds_failed: int = Field(0, description='Number of feeds that failed')
    duplicates_found: int = Field(0, description='Number of duplicates found')
    created_at: datetime = Field(..., description='Job creation timestamp')
    completed_at: Optional[datetime] = Field(None, description='Job completion timestamp')
    error_message: Optional[str] = Field(None, description='Error message if job failed')
    
    class Config:
        schema_extra = {
            'example': {
                'id': 'imp_abc123def456',
                'filename': 'subscriptions.opml',
                'status': 'completed',
                'current_phase': 'cleanup',
                'progress_percentage': 100.0,
                'categories_created': 5,
                'feeds_imported': 25,
                'feeds_failed': 2,
                'duplicates_found': 3,
                'created_at': '2023-12-15T10:30:00Z',
                'completed_at': '2023-12-15T10:32:15Z',
                'error_message': None
            }
        }


class ImportJobStatusResponse(BaseModel):
    '''Detailed import job status response'''
    id: str = Field(..., description='Job identifier')
    user_id: int = Field(..., description='User who created the job')
    filename: str = Field(..., description='Original filename')
    file_size: int = Field(..., description='File size in bytes')
    status: str = Field(..., description='Current job status')
    current_phase: Optional[str] = Field(None, description='Current processing phase')
    current_step: int = Field(0, description='Current step number')
    total_steps: int = Field(0, description='Total number of steps')
    progress_percentage: float = Field(..., description='Progress percentage (0-100)')
    categories_created: int = Field(0, description='Number of categories created')
    feeds_imported: int = Field(0, description='Number of feeds imported')
    feeds_failed: int = Field(0, description='Number of feeds that failed')
    duplicates_found: int = Field(0, description='Number of duplicates found')
    created_at: datetime = Field(..., description='Job creation timestamp')
    started_at: Optional[datetime] = Field(None, description='Job start timestamp')
    completed_at: Optional[datetime] = Field(None, description='Job completion timestamp')
    error_message: Optional[str] = Field(None, description='Error message if job failed')
    error_details: Optional[str] = Field(None, description='Detailed error information')
    
    class Config:
        schema_extra = {
            'example': {
                'id': 'imp_abc123def456',
                'user_id': 123,
                'filename': 'subscriptions.opml',
                'file_size': 1024,
                'status': 'processing',
                'current_phase': 'importing_feeds',
                'current_step': 15,
                'total_steps': 20,
                'progress_percentage': 75.0,
                'categories_created': 3,
                'feeds_imported': 10,
                'feeds_failed': 1,
                'duplicates_found': 2,
                'created_at': '2023-12-15T10:30:00Z',
                'started_at': '2023-12-15T10:30:15Z',
                'completed_at': None,
                'error_message': None,
                'error_details': None
            }
        }


class ImportJobListResponse(BaseModel):
    '''Response for listing import jobs'''
    jobs: List[ImportJobResponse] = Field(..., description='List of import jobs')
    total: int = Field(..., description='Total number of jobs returned')
    
    class Config:
        schema_extra = {
            'example': {
                'jobs': [
                    {
                        'id': 'imp_abc123def456',
                        'filename': 'subscriptions.opml',
                        'status': 'completed',
                        'current_phase': 'cleanup',
                        'progress_percentage': 100.0,
                        'categories_created': 5,
                        'feeds_imported': 25,
                        'feeds_failed': 2,
                        'duplicates_found': 3,
                        'created_at': '2023-12-15T10:30:00Z',
                        'completed_at': '2023-12-15T10:32:15Z',
                        'error_message': None
                    }
                ],
                'total': 1
            }
        }


class ImportJobCancelResponse(BaseModel):
    '''Response for cancelling an import job'''
    job_id: str = Field(..., description='Job identifier that was cancelled')
    message: str = Field(..., description='Confirmation message')
    
    class Config:
        schema_extra = {
            'example': {
                'job_id': 'imp_abc123def456',
                'message': 'Import job cancelled successfully'
            }
        }


class ImportJobErrorResponse(BaseModel):
    '''Error response for import job operations'''
    detail: str = Field(..., description='Error description')
    job_id: Optional[str] = Field(None, description='Job ID if available')
    
    class Config:
        schema_extra = {
            'example': {
                'detail': 'Failed to parse OPML: Invalid XML format',
                'job_id': 'imp_abc123def456'
            }
        }