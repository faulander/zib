from fastapi import APIRouter

from app.services.auto_refresh_service import auto_refresh_service

router = APIRouter(prefix='/refresh', tags=['refresh'])


@router.get('/status', summary='Get Auto-refresh Status')
async def get_refresh_status():
    '''
    Get the current status of the auto-refresh service.
    
    **Response includes:**
    - `status`: Current status (idle, refreshing, completed)
    - `next_refresh_in_seconds`: Seconds until next refresh
    - `last_refresh_time`: ISO timestamp of last refresh
    - `articles_added_last_refresh`: Number of articles added in last refresh
    - `refresh_interval_minutes`: Current refresh interval setting
    
    **Usage:**
    Frontend can poll this endpoint every minute to:
    - Show refresh countdown to users
    - Trigger data refresh when status becomes "completed"
    - Display refresh progress and results
    '''
    return auto_refresh_service.get_refresh_status()