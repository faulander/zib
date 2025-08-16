'''Authentication and authorization utilities'''

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.models.article import User

security = HTTPBearer(auto_error=False)


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    '''
    Get current authenticated user from token
    
    This is a simplified implementation for testing purposes.
    In a real application, you would:
    1. Validate the JWT token
    2. Extract user ID from token
    3. Load user from database
    4. Handle token expiration, etc.
    '''
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For testing purposes, we'll use a simple token check
    # In real implementation, decode and validate JWT token
    token = credentials.credentials
    
    if not token or token != "test-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For testing, return a default user or create one if it doesn't exist
    try:
        # Try to get existing test user
        user = User.get(User.username == 'testuser')
        return user
    except User.DoesNotExist:
        # Create test user for testing purposes
        user = User.create(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password'
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