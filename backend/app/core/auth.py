'''Authentication and authorization utilities'''

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

security = HTTPBearer()


class User(BaseModel):
    '''User model for authentication'''
    id: int
    username: str
    email: Optional[str] = None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    '''
    Get current authenticated user from JWT token
    
    This is a simplified implementation for testing.
    In production, this would validate JWT tokens and fetch user data.
    '''
    # For testing purposes, we'll use a simple token validation
    token = credentials.credentials
    
    if token == 'test-token':
        return User(id=1, username='testuser', email='test@example.com')
    elif token.startswith('user-'):
        # Extract user ID from token like 'user-123'
        try:
            user_id = int(token.split('-')[1])
            return User(id=user_id, username=f'user{user_id}', email=f'user{user_id}@example.com')
        except (IndexError, ValueError):
            pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid authentication credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )