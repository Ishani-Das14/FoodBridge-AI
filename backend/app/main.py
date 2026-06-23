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
from app.services.compliance.router import router as compliance_router
from app.services.csr.router import router as csr_router
from app.services.csr.router import leaderboard_router
from app.services.emergency.router import router as emergency_router
from app.monitoring.health import router as health_router
from app.monitoring.metrics import setup_metrics
from ml.serving.model_registry import registry as model_registry
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT", "production")
)

app = FastAPI(
    title="FoodBridge AI API Gateway",
    description="Backend services powering food redistribution matching and orchestration",
    version="1.0.0",
)

app.add_middleware(SentryAsgiMiddleware)
setup_metrics(app)

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
app.include_router(compliance_router, prefix="/api/v1")
app.include_router(csr_router, prefix="/api/v1")
app.include_router(leaderboard_router, prefix="/api/v1")
app.include_router(emergency_router, prefix="/api/v1/admin")
app.include_router(health_router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
def read_root():
    """System health check ping endpoint."""
    return {
        "status": "healthy",
        "platform": "FoodBridge AI API Gateway",
        "version": "1.0.0"
    }
