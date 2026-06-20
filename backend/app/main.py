# ==============================================================================
# FoodBridge AI - API Gateway Entrypoint (main.py)
# Initializes FastAPI, loads middleware configurations, and maps router paths
# ==============================================================================
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.services.donation.router import router as donation_router, restaurant_router
from app.services.matching.router import router as matching_router
from app.services.ml.freshness_router import router as freshness_router
from app.services.ml.forecast_router import router as forecast_router
from app.services.ml.routing_router import router as routing_router
from app.services.analytics.router import router as analytics_router
from app.services.notifications.router import router as notification_router
from app.services.admin.router import router as admin_router
from ml.serving.model_registry import registry as model_registry

app = FastAPI(
    title="FoodBridge AI API Gateway",
    description="Backend services powering food redistribution matching and orchestration",
    version="1.0.0",
)

# ------------------------------------------------------------------------------
# Cross-Origin Resource Sharing (CORS) Middleware Setup
# ------------------------------------------------------------------------------
BACKEND_CORS_ORIGINS = os.getenv(
    "BACKEND_CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:8000"
)

origins = [origin.strip() for origin in BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# API Sub-Router Registry
# ------------------------------------------------------------------------------
# Register authorization endpoints under standard v1 schema
app.include_router(auth_router, prefix="/api/v1")
app.include_router(donation_router, prefix="/api/v1")
app.include_router(restaurant_router, prefix="/api/v1")
app.include_router(matching_router, prefix="/api/v1")
app.include_router(freshness_router, prefix="/api/v1")
app.include_router(forecast_router, prefix="/api/v1")
app.include_router(routing_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

@app.get("/api/v1/ml/health", tags=["Machine Learning"])
def get_ml_health():
    """Returns the health status of all pre-loaded ML models."""
    return model_registry.health_check()

@app.get("/", tags=["Health Check"])
def read_root():
    """System health check ping endpoint."""
    return {
        "status": "healthy",
        "platform": "FoodBridge AI API Gateway",
        "version": "1.0.0"
    }
