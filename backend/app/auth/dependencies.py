# ==============================================================================
# FoodBridge AI - Security Dependencies
# Implements extraction of security credentials and Role-Based Access Control (RBAC)
# ==============================================================================
from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User

# Standard HTTP Authorization Header Scheme (expects Bearer token)
security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
    token: str = None
) -> User:
    """
    Decodes the JWT access token and returns the authenticated user context.
    Raises HTTP 401 Unauthorized if the token is missing, expired, or invalid.
    """
    if token is None:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization credentials are missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = credentials.credentials
    claims = decode_token(token)
    
    # Verify signature output contains claims
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract identity subject (User ID) from 'sub' claim
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is corrupted: identifier is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Query corresponding database model
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this session no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your account has been deactivated. Contact administration.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

class RoleRequired:
    """Dependency factory checking user clearance for Role-Based Access Control (RBAC)."""
    def __init__(self, allowed_role: str):
        self.allowed_role = allowed_role

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        Validates the user's role against permissions requirements.
        Raises HTTP 403 Forbidden if the user lacks clearance.
        """
        if current_user.role != self.allowed_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: This portal requires a '{self.allowed_role}' account clearance."
            )
        return current_user

def role_required(role: str) -> RoleRequired:
    """Convenience helper generating RBAC validator instances for routing dependencies."""
    return RoleRequired(role)
