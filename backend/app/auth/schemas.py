# ==============================================================================
# FoodBridge AI - Authentication Schemas
# Defines Pydantic data validation and serialization models for API boundaries
# ==============================================================================
import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

# ------------------------------------------------------------------------------
# Registration Request Models
# ------------------------------------------------------------------------------
class RestaurantRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    name: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=5)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class NGORegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    name: str = Field(..., min_length=2, max_length=100)
    registration_number: str = Field(..., min_length=3, description="Official state/federal registration code")
    address: str = Field(..., min_length=5)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class VolunteerRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., min_length=7, description="Contact phone number")
    vehicle_type: Optional[str] = Field(None, description="Transport medium: car, bike, foot, etc.")

# ------------------------------------------------------------------------------
# Login & Token Models
# ------------------------------------------------------------------------------
class LoginPayload(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# ------------------------------------------------------------------------------
# Profile Response Models
# ------------------------------------------------------------------------------
class RestaurantProfileOut(BaseModel):
    id: int
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True

class NGOProfileOut(BaseModel):
    id: int
    name: str
    registration_number: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True

class VolunteerProfileOut(BaseModel):
    id: int
    name: str
    phone_number: str
    vehicle_type: Optional[str] = None

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime.datetime
    restaurant_profile: Optional[RestaurantProfileOut] = None
    ngo_profile: Optional[NGOProfileOut] = None
    volunteer_profile: Optional[VolunteerProfileOut] = None

    class Config:
        from_attributes = True
