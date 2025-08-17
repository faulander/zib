'''Authentication and authorization utilities'''

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.models.article import User

security = HTTPBearer(auto_error=False)


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    '''
    Get current user for single-user system
    
    This system is designed for single-user use, so we always return
    the default user without requiring authentication.
    '''
    
    # Single-user system: always return the default user
    try:
        # Try to get existing default user
        user = User.get(User.username == 'default')
        return user
    except User.DoesNotExist:
        # Create default user for single-user system
        user = User.create(
            username='default',
            email='user@localhost',
            password_hash='no_password_needed'
        )
        return user


def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    '''
    Get current user if authenticated, None otherwise
    Used for endpoints that work for both authenticated and unauthenticated users
    '''
    
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None