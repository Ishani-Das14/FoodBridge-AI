import os
import json
import joblib
import pandas as pd
from typing import Dict, Any

import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(project_root)

from ml.features.engineering import FeatureEngineer

class FreshnessPredictor:
    """
    Singleton-like wrapper for the pre-trained freshness XGBoost pipeline.
    Ensures the model and feature names are loaded only once.
    """
    
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            model_dir = os.path.dirname(__file__)
            
        model_path = os.path.join(model_dir, "freshness_model.pkl")
        names_path = os.path.join(model_dir, "feature_names.json")
        
        # Load the pipeline
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. Please run train.py first.")
        self.model = joblib.load(model_path)
        
        # Load the feature names (to ensure consistent column order during inference)
        if not os.path.exists(names_path):
            raise FileNotFoundError(f"Feature names file not found at {names_path}. Please run train.py first.")
        with open(names_path, "r") as f:
            self.feature_names = json.load(f)
            
        self.fe = FeatureEngineer()

    def predict(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts if the food donation is safe for delivery.
        
        Input should contain:
        - food_type: str
        - quantity: int/float
        - expiry_minutes: int/float
        - distance_km: float
        - weather_temp: float
        - ngo_capacity: int/float
        - traffic_factor: float
        - prep_time_hour: int (optional, default 12)
        """
        # Ensure minimum required fields exist with defaults
        if "prep_time_hour" not in input_dict:
            input_dict["prep_time_hour"] = 12

        # Convert to single-row dataframe
        df = pd.DataFrame([input_dict])
        
        # Apply the feature engineering pipeline
        X_df, _ = self.fe.transform(df)
        
        # Reorder and pad columns to exactly match what the model was trained on
        # (Handling missing dummy columns for categorical features unseen at inference)
        for col in self.feature_names:
            if col not in X_df.columns:
                X_df[col] = 0
                
        # Slice only the required columns in the correct order
        X = X_df[self.feature_names].values
        
        # Get probability of class 1 (on-time / safe)
        prob_safe = float(self.model.predict_proba(X)[0][1])
        is_safe = prob_safe >= 0.5
        
        # Determine risk level
        if prob_safe > 0.8:
            risk_level = "low"
        elif prob_safe > 0.4:
            risk_level = "medium"
        else:
            risk_level = "high"
            
        # Determine business reason logic
        distance_km = float(input_dict.get("distance_km", 0))
        weather_temp = float(input_dict.get("weather_temp", 25))
        
        # Calculate time_to_expiry exactly as FeatureEngineer does
        time_buffer = self.fe.time_to_expiry(df.iloc[0])
        
        reason = "Food can be safely delivered"
        if not is_safe or risk_level != "low":
            if distance_km > 15:
                reason = "Distance too high for safe delivery"
            elif weather_temp > 38:
                reason = "High temperature accelerates spoilage"
            elif time_buffer < 20:
                reason = "Insufficient time buffer before expiry"
            else:
                reason = "Risk factors (traffic/expiry/distance) combine to make delivery unsafe"
                
        return {
            "is_safe": bool(is_safe),
            "confidence": prob_safe,
            "risk_level": risk_level,
            "reason": reason
        }
