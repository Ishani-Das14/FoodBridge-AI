# ==============================================================================
# FoodBridge AI - Donation Service Schemas
# Defines Pydantic data validation and serialization models for food donations
# ==============================================================================
import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

class DonationCreate(BaseModel):
    food_type: str = Field(..., min_length=2, max_length=100, description="Type of food, e.g. Bakery goods, Hot meals")
    quantity: str = Field(..., min_length=1, description="Quantity and units, e.g. 10 kg, 15 meals")
    prep_time: datetime.datetime = Field(..., description="Timestamp when the food was prepared/ready")
    expiry_minutes: int = Field(..., gt=0, description="Lifespan of the food in minutes from preparation time")
    pickup_address: str = Field(..., min_length=5, description="Full pickup location address")
    pickup_lat: float = Field(..., ge=-90.0, le=90.0, description="Pickup location latitude")
    pickup_lng: float = Field(..., ge=-180.0, le=180.0, description="Pickup location longitude")

class DonationStatusUpdate(BaseModel):
    status: Literal["picked_up", "delivered", "expired"] = Field(..., description="New status value")

class DonationOut(BaseModel):
    id: int
    restaurant_id: int
    food_type: str
    quantity: str
    prep_time: datetime.datetime
    expiry_time: datetime.datetime
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    status: str
    created_at: datetime.datetime
    restaurant_name: str

    class Config:
        from_attributes = True
