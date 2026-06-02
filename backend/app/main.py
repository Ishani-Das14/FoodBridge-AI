# ==============================================================================
# FoodBridge AI - API Gateway Entrypoint (main.py)
# Initializes FastAPI, loads middleware configurations, and maps router paths
# ==============================================================================
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.services.donation.router import router as donation_router

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
    "http://localhost:3000,http://localhost:5173,http://localhost:8000"
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

@app.get("/", tags=["Health Check"])
def read_root():
    """System health check ping endpoint."""
    return {
        "status": "healthy",
        "platform": "FoodBridge AI API Gateway",
        "version": "1.0.0"
    }
