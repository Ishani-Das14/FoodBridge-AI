# ==============================================================================
# FoodBridge AI - Security Configuration
# Manages password encryption and JSON Web Token (JWT) workflows
# ==============================================================================
import os
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt, JWTError
import bcrypt

# Retrieve security parameters from environmental configurations
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretjwtkeythatshouldbechangedinproduction123!")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")) # Default 30 min
REFRESH_TOKEN_EXPIRE_DAYS = 7 # Required 7 days

def hash_password(password: str) -> str:
    """Computes a cryptographically secure hash from a plain text password."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Validates a candidate plain text password against a stored hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(subject: Union[str, Any], role: str, email: str, expires_delta: timedelta = None) -> str:
    """Generates an access JWT with a 30-minute default lifetime."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject), # sub is typically the user_id in OAuth2/JWT
        "role": role,
        "email": email
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(subject: Union[str, Any], role: str, email: str, expires_delta: timedelta = None) -> str:
    """Generates a long-lived refresh JWT with a 7-day default lifetime."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "email": email,
        "type": "refresh"
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decodes a JWT and verifies its signature, returning the claims dictionary."""
    try:
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_payload
    except JWTError:
        return {}
