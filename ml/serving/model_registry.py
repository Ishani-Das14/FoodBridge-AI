import os
import sys
import logging
from typing import Dict, Optional

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

from ml.models.freshness.predict import FreshnessPredictor
from ml.models.forecasting.prophet_model import ProphetForecaster
from ml.models.routing.vrp_solver import VRPSolver

logger = logging.getLogger(__name__)

class ModelRegistry:
    """
    Singleton class to load and serve ML models at app startup.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self._freshness_model: Optional[FreshnessPredictor] = None
        self._forecaster: Optional[ProphetForecaster] = None
        self._vrp_solver: Optional[VRPSolver] = None
        
        self.health_status = {
            "freshness": "uninitialized",
            "forecaster": "uninitialized",
            "vrp": "uninitialized"
        }
        
        self._load_models()
        self._initialized = True
        
    def _load_models(self):
        # 1. Freshness Predictor
        try:
            self._freshness_model = FreshnessPredictor()
            # Try to force a lazy load to check if model exists
            _ = self._freshness_model._get_model()
            self.health_status["freshness"] = "ok"
            logger.info("Loaded FreshnessPredictor successfully.")
        except Exception as e:
            self.health_status["freshness"] = "error"
            logger.error(f"Failed to load FreshnessPredictor: {e}")
            
        # 2. Prophet Forecaster
        try:
            models_dir = os.path.join(project_root, "ml", "models", "forecasting")
            self._forecaster = ProphetForecaster(model_dir=models_dir)
            self.health_status["forecaster"] = "ok"
            logger.info("Loaded ProphetForecaster successfully.")
        except Exception as e:
            self.health_status["forecaster"] = "error"
            logger.error(f"Failed to load ProphetForecaster: {e}")
            
        # 3. VRP Solver
        try:
            self._vrp_solver = VRPSolver()
            self.health_status["vrp"] = "ok"
            logger.info("Loaded VRPSolver successfully.")
        except Exception as e:
            self.health_status["vrp"] = "error"
            logger.error(f"Failed to load VRPSolver: {e}")

    def get_freshness_model(self) -> FreshnessPredictor:
        if not self._freshness_model:
            raise RuntimeError("FreshnessPredictor is not loaded.")
        return self._freshness_model

    def get_forecaster(self) -> ProphetForecaster:
        if not self._forecaster:
            raise RuntimeError("ProphetForecaster is not loaded.")
        return self._forecaster

    def get_vrp_solver(self) -> VRPSolver:
        if not self._vrp_solver:
            raise RuntimeError("VRPSolver is not loaded.")
        return self._vrp_solver

    def health_check(self) -> Dict[str, str]:
        return self.health_status

# Global instance
registry = ModelRegistry()
