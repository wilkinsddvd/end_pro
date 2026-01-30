"""
JWT Authentication Utilities

This module provides functions for creating and validating JWT tokens
for Bearer token authentication.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
from db import get_async_db

# JWT Configuration - using environment variables with sensible defaults for dev
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

# Warn if using default secret key
if SECRET_KEY == "dev-secret-key-change-in-production":
    import warnings
    warnings.warn(
        "Using default JWT_SECRET_KEY! Set JWT_SECRET_KEY environment variable in production.",
        RuntimeWarning
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing claims to encode (e.g., {"sub": user_id, "username": username})
        expires_delta: Optional custom expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded token payload if valid, None if invalid or expired
        
    Note:
        Returns None for both expired and invalid tokens. The caller should
        handle authentication failures appropriately.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired - could be logged for monitoring
        return None
    except jwt.InvalidTokenError:
        # Invalid token - could indicate tampering
        return None


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT token.
    
    Extracts the Bearer token from Authorization header, validates it,
    and returns the corresponding User object from the database.
    
    Args:
        authorization: Authorization header containing "Bearer <token>"
        db: Database session
        
    Returns:
        User object if authentication successful
        
    Raises:
        HTTPException with 401 status if authentication fails
    """
    # Check if Authorization header is present
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={"code": 401, "data": {}, "msg": "authorization header missing"}
        )
    
    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail={"code": 401, "data": {}, "msg": "invalid authorization header format"}
        )
    
    token = parts[1]
    
    # Decode and validate token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail={"code": 401, "data": {}, "msg": "invalid or expired token"}
        )
    
    # Extract user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail={"code": 401, "data": {}, "msg": "invalid token payload"}
        )
    
    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"code": 401, "data": {}, "msg": "user not found"}
        )
    
    return user
