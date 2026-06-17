import os
import sys
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(project_root)

from ml.models.forecasting.prophet_model import ProphetForecaster
from app.core.redis import redis_client

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

# Singleton forecaster
prophet_instance = None

def get_prophet():
    global prophet_instance
    if prophet_instance is None:
        try:
            # Point to the models directory where models are saved
            models_dir = os.path.join(project_root, "ml", "models", "forecasting")
            prophet_instance = ProphetForecaster(model_dir=models_dir)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load forecasting models: {e}")
    return prophet_instance

@router.get("/demand-forecast")
def get_demand_forecast(
    ngo_id: str = Query(..., description="ID of the NGO"),
    date: str = Query(..., description="Target date (YYYY-MM-DD)")
):
    """
    Predicts food demand for a specific NGO using the pre-trained Prophet model.
    """
    forecaster = get_prophet()
    
    # Check if model exists (since our NGOs are string '1' to '5')
    if ngo_id not in ["1", "2", "3", "4", "5"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"NGO {ngo_id} not found or no model trained.")
        
    try:
        # Predict 1 day ahead
        # (Assuming the training data ends 'today', we just request a 1-day prediction)
        # Note: In a real system, you'd calculate days_ahead = (target_date - last_train_date).days
        result = forecaster.predict(ngo_id=ngo_id, days_ahead=1)
        
        # Override the result date with requested date for simplicity
        result["date"] = date
        result["model"] = "prophet"
        return result
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Forecast failed: {e}")

@router.get("/demand-forecast/all")
def get_all_demand_forecasts(
    date: str = Query(..., description="Target date (YYYY-MM-DD)")
):
    """
    Runs forecast for all 5 simulated NGOs and caches the result.
    """
    cache_key = f"forecast:{date}"
    
    # Try cache first
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    forecaster = get_prophet()
    results = []
    
    for ngo_id in ["1", "2", "3", "4", "5"]:
        try:
            res = forecaster.predict(ngo_id=ngo_id, days_ahead=1)
            res["date"] = date
            res["model"] = "prophet"
            results.append(res)
        except FileNotFoundError:
            continue
            
    # Save to cache with TTL 3600 (1 hour)
    if redis_client and results:
        try:
            redis_client.setex(cache_key, 3600, json.dumps(results))
        except Exception:
            pass
            
    return results
