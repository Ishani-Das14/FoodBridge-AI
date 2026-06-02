# ==============================================================================
# FoodBridge AI - Celery Orchestration Center (celery_app.py)
# Initializes Celery client and binds Redis broker and results backend
# ==============================================================================
import os
from celery import Celery

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

# Setup primary Celery instance matching uvicorn/beat runner hooks
celery_app = Celery(
    "foodbridge_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    imports=("app.tasks.donation_tasks",) # Explicitly load tasks to register them
)
