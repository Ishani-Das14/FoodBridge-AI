# ==============================================================================
# FoodBridge AI - Matching Service Schemas
# Defines Pydantic data validation and serialization models for donation matching
# ==============================================================================
import datetime
from pydantic import BaseModel, Field

class MatchOut(BaseModel):
    id: int = Field(..., description="Unique match identifier")
    donation_id: int = Field(..., description="Referenced donation identifier")
    ngo_id: int = Field(..., description="Referenced NGO profile identifier")
    quantity_allocated: int = Field(..., description="Quantity of food allocated to the NGO")
    status: str = Field(..., description="Current status of the match: pending, accepted, rejected")
    created_at: datetime.datetime = Field(..., description="Timestamp of match record creation")

    class Config:
        from_attributes = True
