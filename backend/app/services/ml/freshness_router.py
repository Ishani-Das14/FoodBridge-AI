from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(project_root)

from ml.models.freshness.predict import FreshnessPredictor

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

# Module-level singleton
predictor_instance = None

def get_predictor():
    global predictor_instance
    if predictor_instance is None:
        try:
            predictor_instance = FreshnessPredictor()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load ML model: {e}")
    return predictor_instance

class FreshnessRequest(BaseModel):
    food_type: str = Field(..., description="Type of food (e.g., Rice, Roti)")
    quantity: float = Field(..., description="Quantity or number of packs")
    expiry_minutes: float = Field(..., description="Estimated minutes until expiry")
    distance_km: float = Field(..., description="Delivery distance in km")
    weather_temp: float = Field(..., description="Ambient weather temperature in C")
    ngo_capacity: float = Field(..., description="Receiving NGO capacity")
    traffic_factor: float = Field(..., description="Traffic multiplier (e.g., 1.0, 1.5)")

class FreshnessResponse(BaseModel):
    is_safe: bool
    confidence: float
    risk_level: str
    reason: str

@router.post("/freshness-check", response_model=FreshnessResponse)
def check_freshness(request: FreshnessRequest):
    """
    Predicts if a food donation will remain fresh during delivery using the XGBoost model.
    """
    predictor = get_predictor()
    try:
        result = predictor.predict(request.model_dump())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}"
        )
