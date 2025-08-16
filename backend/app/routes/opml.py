'''OPML import API routes'''

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    UploadFile, 
    File, 
    Form, 
    status,
    Query
)
from typing import Optional, List
from loguru import logger

from app.schemas.opml import (
    ImportJobResponse,
    ImportJobStatusResponse,
    ImportJobListResponse,
    ImportJobCreateResponse,
    ImportJobCancelResponse
)
from app.services.opml import (
    import_processor,
    import_manager,
    ImportProcessorError,
    ImportStatus
)
from app.core.auth import get_current_user


router = APIRouter(prefix='/api/import', tags=['OPML Import'])


@router.post('/opml', 
            response_model=ImportJobCreateResponse,
            status_code=status.HTTP_202_ACCEPTED,
            summary='Import OPML file',
            description='Upload and import an OPML file containing RSS feed subscriptions')
async def import_opml(
    file: UploadFile = File(..., description='OPML file to import'),
    duplicate_strategy: str = Form('skip', description='How to handle duplicate feeds (skip, merge, replace)'),
    validate_feeds: bool = Form(True, description='Whether to validate feed URLs'),
    merge_categories: bool = Form(True, description='Whether to merge duplicate categories'),
    category_parent_id: Optional[int] = Form(None, description='Parent category ID for all imported categories'),
    current_user = Depends(get_current_user)
) -> ImportJobCreateResponse:
    '''
    Import an OPML file containing RSS feed subscriptions.
    
    The import process runs asynchronously. Use the returned job_id to track progress.
    '''
    # Validate file type
    if not file.content_type or file.content_type not in ['application/xml', 'text/xml', 'application/opml+xml']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid file type. Only XML/OPML files are supported.'
        )
    
    # Check file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail='File too large. Maximum size is 5MB.'
        )
    
    try:
        # Prepare import options
        options = {
            'duplicate_strategy': duplicate_strategy,
            'validate_feeds': validate_feeds,
            'merge_categories': merge_categories,
            'category_parent_id': category_parent_id
        }
        
        # Start import process
        result = await import_processor.process_import(
            user_id=current_user.id,
            opml_content=content.decode('utf-8'),
            filename=file.filename or 'unknown.opml',
            options=options
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error_message or 'Import failed',
                headers={'X-Job-ID': result.job_id}
            )
        
        logger.info(f'OPML import started for user {current_user.id}: job {result.job_id}')
        
        return ImportJobCreateResponse(
            job_id=result.job_id,
            message='OPML import started successfully',
            status='processing'
        )
        
    except ImportProcessorError as e:
        logger.error(f'Import processor error for user {current_user.id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid file encoding. File must be UTF-8 encoded.'
        )
    except Exception as e:
        logger.error(f'Unexpected error during OPML import for user {current_user.id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='An unexpected error occurred during import'
        )


@router.get('/jobs/{job_id}',
           response_model=ImportJobStatusResponse,
           summary='Get import job status',
           description='Get the current status and progress of an import job')
async def get_import_job(
    job_id: str,
    current_user = Depends(get_current_user)
) -> ImportJobStatusResponse:
    '''
    Get the status and progress of a specific import job.
    '''
    try:
        job = import_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Import job not found'
            )
        
        # Check if user owns this job (if user_id is available in job model)
        # For now, we'll allow any authenticated user to view any job
        # TODO: Add proper user authorization when user_id is added to ImportJob model
        
        # Calculate progress percentage
        progress_percentage = 0.0
        if job.total_steps and job.total_steps > 0:
            progress_percentage = (job.current_step / job.total_steps) * 100
        
        return ImportJobStatusResponse(
            id=job.id,
            user_id=job.user_id,
            filename=job.filename,
            file_size=job.file_size,
            status=job.status,
            current_phase=job.current_phase,
            current_step=job.current_step,
            total_steps=job.total_steps,
            progress_percentage=progress_percentage,
            categories_created=job.categories_created,
            feeds_imported=job.feeds_imported,
            feeds_failed=job.feeds_failed,
            duplicates_found=job.duplicates_found,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            error_details=job.error_details
        )
        
    except Exception as e:
        logger.error(f'Error retrieving import job {job_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve import job status'
        )


@router.get('/jobs',
           response_model=ImportJobListResponse,
           summary='List import jobs',
           description='List import jobs with optional filtering')
async def list_import_jobs(
    status_filter: Optional[str] = Query(None, alias='status', description='Filter by job status'),
    limit: int = Query(50, ge=1, le=100, description='Maximum number of jobs to return'),
    current_user = Depends(get_current_user)
) -> ImportJobListResponse:
    '''
    List import jobs for the current user with optional filtering.
    '''
    try:
        # Parse status filter
        status_enum = None
        if status_filter:
            try:
                status_enum = ImportStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Invalid status filter: {status_filter}'
                )
        
        # Get jobs from import manager
        jobs = import_manager.list_jobs(
            user_id=current_user.id,
            status=status_enum,
            limit=limit
        )
        
        # Convert to response format
        job_responses = []
        for job in jobs:
            progress_percentage = 0.0
            if job.total_steps and job.total_steps > 0:
                progress_percentage = (job.current_step / job.total_steps) * 100
            
            job_responses.append(ImportJobResponse(
                id=job.id,
                filename=job.filename,
                status=job.status,
                current_phase=job.current_phase,
                progress_percentage=progress_percentage,
                categories_created=job.categories_created,
                feeds_imported=job.feeds_imported,
                feeds_failed=job.feeds_failed,
                duplicates_found=job.duplicates_found,
                created_at=job.created_at,
                completed_at=job.completed_at,
                error_message=job.error_message
            ))
        
        return ImportJobListResponse(
            jobs=job_responses,
            total=len(job_responses)
        )
        
    except Exception as e:
        logger.error(f'Error listing import jobs for user {current_user.id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve import jobs'
        )


@router.delete('/jobs/{job_id}',
              response_model=ImportJobCancelResponse,
              summary='Cancel import job',
              description='Cancel a running import job')
async def cancel_import_job(
    job_id: str,
    current_user = Depends(get_current_user)
) -> ImportJobCancelResponse:
    '''
    Cancel a running import job.
    
    Only jobs in 'pending' or 'processing' status can be cancelled.
    '''
    try:
        # Check if job exists and user has access
        job = import_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Import job not found'
            )
        
        # TODO: Check if user owns this job when user_id is available
        
        # Attempt to cancel the job
        success = import_manager.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Cannot cancel import job. Job may already be completed or cancelled.'
            )
        
        logger.info(f'Import job {job_id} cancelled by user {current_user.id}')
        
        return ImportJobCancelResponse(
            job_id=job_id,
            message='Import job cancelled successfully'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error cancelling import job {job_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to cancel import job'
        )