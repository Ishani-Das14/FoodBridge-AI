# ==============================================================================
# FoodBridge AI - Authentication Router
# Exposes REST endpoints for user onboarding, token issuance, and sessions
# ==============================================================================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models import User
from app.auth.schemas import (
    RestaurantRegister,
    NGORegister,
    VolunteerRegister,
    LoginPayload,
    TokenResponse,
    TokenRefreshRequest,
    UserOut
)
from app.auth.service import (
    register_restaurant_user,
    register_ngo_user,
    register_volunteer_user,
    authenticate_user,
    store_refresh_token,
    get_cached_refresh_token,
    revoke_refresh_token
)
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ------------------------------------------------------------------------------
# Registration Endpoints
# ------------------------------------------------------------------------------
@router.post("/register/restaurant", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_restaurant(data: RestaurantRegister, db: Session = Depends(get_db)):
    """Registers a restaurant partner account with profile metadata."""
    return register_restaurant_user(db, data)

@router.post("/register/ngo", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_ngo(data: NGORegister, db: Session = Depends(get_db)):
    """Registers a charity/NGO organization partner account with state registration code."""
    return register_ngo_user(db, data)

@router.post("/register/volunteer", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_volunteer(data: VolunteerRegister, db: Session = Depends(get_db)):
    """Registers an individual volunteer delivery partner account."""
    return register_volunteer_user(db, data)

# ------------------------------------------------------------------------------
# Session Endpoints (Login, Refresh, Profile)
# ------------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    """
    Authenticates user credentials and issues matching access & refresh tokens.
    Refresh token is registered and cached within Redis for 7 days.
    """
    user = authenticate_user(db, payload)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your account has been deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate Access (30 mins) and Refresh (7 days) Tokens
    access_token = create_access_token(subject=user.id, role=user.role, email=user.email)
    refresh_token = create_refresh_token(subject=user.id, role=user.role, email=user.email)

    # Store in Redis
    store_refresh_token(user.id, refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_session(payload: TokenRefreshRequest, db: Session = Depends(get_db)):
    """
    Exchanges a valid, cached refresh token for a new set of session tokens.
    Implements single-active-session refresh token validation via Redis.
    """
    token_claims = decode_token(payload.refresh_token)
    
    # 1. Verify token authenticity
    if not token_claims or token_claims.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided refresh token is invalid or expired."
        )
    
    user_id = token_claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token payload is corrupted."
        )
        
    # 2. Check if the token matches the active refresh token cached in Redis
    cached_token = get_cached_refresh_token(user_id)
    if not cached_token or cached_token != payload.refresh_token:
        # Revoke the session immediately for security in case of token hijacking
        revoke_refresh_token(user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is revoked, stale, or hijacked. Please re-authenticate."
        )
        
    # 3. Retrieve database user context
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token is suspended or no longer exists."
        )

    # 4. Generate new session tokens
    new_access = create_access_token(subject=user.id, role=user.role, email=user.email)
    new_refresh = create_refresh_token(subject=user.id, role=user.role, email=user.email)

    # 5. Overwrite the cache in Redis
    store_refresh_token(user.id, new_refresh)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh
    )

@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """Returns the profile metadata of the currently authenticated session user."""
    return current_user
