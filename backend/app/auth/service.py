# ==============================================================================
# FoodBridge AI - Authentication Service
# Manages user accounts creation, authentication, and Redis refresh token caching
# ==============================================================================
import os
import logging
from typing import Optional
import redis
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import User, RestaurantProfile, NGOProfile, VolunteerProfile
from app.core.security import hash_password, verify_password
from app.auth.schemas import RestaurantRegister, NGORegister, VolunteerRegister, LoginPayload

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Redis Cache Client Connection Setup
# ------------------------------------------------------------------------------
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=3
    )
except Exception as e:
    logger.error(f"Failed to initialize Redis connection: {e}")
    redis_client = None

# ------------------------------------------------------------------------------
# Redis Token Cache Helpers
# ------------------------------------------------------------------------------
def store_refresh_token(user_id: int, refresh_token: str) -> None:
    """Caches the refresh token in Redis with a 7-day Time-To-Live (TTL)."""
    if redis_client is None:
        logger.warning("Redis is offline - refresh token was not cached.")
        return
    
    key = f"foodbridge:refresh_token:{user_id}"
    try:
        # 7 days in seconds = 7 * 24 * 60 * 60 = 604800 seconds
        redis_client.setex(key, 604800, refresh_token)
    except redis.RedisError as e:
        logger.error(f"Redis write failure storing token for user {user_id}: {e}")
        # Note: In production we could raise an error, but let's be robust and try to proceed

def get_cached_refresh_token(user_id: int) -> Optional[str]:
    """Retrieves the cached refresh token from Redis for validation."""
    if redis_client is None:
        logger.warning("Redis is offline - cannot fetch cached refresh token.")
        return None
    
    key = f"foodbridge:refresh_token:{user_id}"
    try:
        return redis_client.get(key)
    except redis.RedisError as e:
        logger.error(f"Redis fetch failure retrieving token for user {user_id}: {e}")
        return None

def revoke_refresh_token(user_id: int) -> None:
    """Clears the cached refresh token from Redis (e.g., during logout)."""
    if redis_client is None:
        return
    key = f"foodbridge:refresh_token:{user_id}"
    try:
        redis_client.delete(key)
    except redis.RedisError as e:
        logger.error(f"Redis deletion failure for user {user_id}: {e}")

# ------------------------------------------------------------------------------
# Core Account Operations
# ------------------------------------------------------------------------------
def check_email_exists(db: Session, email: str) -> bool:
    """Verifies whether an email address is already bound to a user account."""
    return db.query(User).filter(User.email == email).first() is not None

def register_restaurant_user(db: Session, data: RestaurantRegister) -> User:
    """Registers a restaurant user and initializes their profile within a transaction."""
    if check_email_exists(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # 1. Create base user record
    hashed_pwd = hash_password(data.password)
    user = User(
        email=data.email,
        hashed_password=hashed_pwd,
        role="restaurant",
        is_active=True
    )
    db.add(user)
    db.flush() # Flushes changes to populate user.id prior to committing

    # 2. Bind restaurant profile
    profile = RestaurantProfile(
        user_id=user.id,
        name=data.name,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user

def register_ngo_user(db: Session, data: NGORegister) -> User:
    """Registers an NGO user and initializes their profile within a transaction."""
    if check_email_exists(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )
    
    # Verify uniqueness of NGO registration code
    existing_reg = db.query(NGOProfile).filter(NGOProfile.registration_number == data.registration_number).first()
    if existing_reg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An NGO profile with this registration number already exists."
        )

    # 1. Create base user record
    hashed_pwd = hash_password(data.password)
    user = User(
        email=data.email,
        hashed_password=hashed_pwd,
        role="ngo",
        is_active=True
    )
    db.add(user)
    db.flush()

    # 2. Bind NGO profile
    profile = NGOProfile(
        user_id=user.id,
        name=data.name,
        registration_number=data.registration_number,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user

def register_volunteer_user(db: Session, data: VolunteerRegister) -> User:
    """Registers a volunteer user and initializes their profile within a transaction."""
    if check_email_exists(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # 1. Create base user record
    hashed_pwd = hash_password(data.password)
    user = User(
        email=data.email,
        hashed_password=hashed_pwd,
        role="volunteer",
        is_active=True
    )
    db.add(user)
    db.flush()

    # 2. Bind volunteer profile
    profile = VolunteerProfile(
        user_id=user.id,
        name=data.name,
        phone_number=data.phone_number,
        vehicle_type=data.vehicle_type
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, payload: LoginPayload) -> Optional[User]:
    """Retrieves a user by email and verifies their password, returning the User object if valid."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return None
    if not verify_password(payload.password, user.hashed_password):
        return None
    return user
