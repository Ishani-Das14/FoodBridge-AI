import time
from fastapi import APIRouter, status, Response
from sqlalchemy import text
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(project_root)

from backend.app.core.database import SessionLocal
from backend.app.core.redis import redis_client
from backend.app.tasks.celery_app import celery_app
from ml.serving.model_registry import registry as model_registry

router = APIRouter(tags=["Monitoring & Health"])

@router.get("/health")
def health_check(response: Response):
    """
    Deep health check for DB, Redis, and Celery connectivity.
    Each check operates with strict fast timeouts.
    """
    timestamp = time.time()
    checks = {"postgresql": False, "redis": False, "celery": False}
    overall_status = "healthy"
    
    # 1. PostgreSQL Check
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        checks["postgresql"] = True
    except Exception:
        overall_status = "degraded"
    finally:
        try:
            db.close()
        except:
            pass
        
    # 2. Redis Check
    if redis_client:
        try:
            checks["redis"] = redis_client.ping()
        except Exception:
            overall_status = "degraded"
            
    # 3. Celery Check
    try:
        # Check if at least 1 worker responds to ping, with a strict 2s timeout
        i = celery_app.control.inspect(timeout=2.0)
        active_workers = i.ping() if i else None
        if active_workers and len(active_workers) > 0:
            checks["celery"] = True
        else:
            overall_status = "degraded"
    except Exception:
        overall_status = "degraded"
        
    if not all(checks.values()):
        overall_status = "degraded"
        # Reject with 503 if ANY check fails, as per requirement
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "down"
        
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": timestamp
    }

@router.get("/health/ml")
def get_ml_health():
    """
    Returns model loading status for freshness, forecaster, vrp models.
    """
    return model_registry.health_check()
