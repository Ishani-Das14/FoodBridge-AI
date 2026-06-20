import os
import sys
import json
from fastapi import APIRouter, Depends, HTTPException
from celery.result import AsyncResult

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(project_root)

from backend.app.auth.dependencies import role_required
from backend.app.tasks.retrain_tasks import retrain_freshness_model
from backend.app.models import User

router = APIRouter(prefix="/admin", tags=["Admin ML Operations"])

@router.post("/retrain-models")
def trigger_manual_retrain(current_user: User = Depends(role_required("government"))):
    """
    Manually triggers retrain_freshness_model Celery task.
    """
    task = retrain_freshness_model.delay()
    return {"task_id": task.id, "status": "queued"}

@router.get("/model-history")
def get_model_history(current_user: User = Depends(role_required("government"))):
    """
    Reads model_history.json and returns all past retraining decisions.
    """
    history_file = os.path.join(project_root, "ml", "models", "freshness", "model_history.json")
    if not os.path.exists(history_file):
        return []
        
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
        # Return newest first
        return sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read history: {e}")

@router.get("/retrain-status/{task_id}")
def get_retrain_status(task_id: str, current_user: User = Depends(role_required("government"))):
    """
    Check Celery task status using AsyncResult.
    """
    task_result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
