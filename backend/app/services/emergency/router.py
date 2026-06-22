import os
import sys
from pydantic import BaseModel
from typing import List
from fastapi import APIRouter, Depends, HTTPException

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(project_root)

from app.core.database import get_db
from app.auth.dependencies import role_required, get_current_user
from sqlalchemy.orm import Session
from app.models import User
from app.services.emergency.service import EmergencyModeService

router = APIRouter(prefix="/emergency-mode", tags=["Emergency Protocol"])

class ActivateRequest(BaseModel):
    reason: str
    affected_districts: List[str]

@router.post("/activate", dependencies=[Depends(role_required("government"))])
def activate_emergency(request: ActivateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Activates emergency mode, expands radius, and alerts volunteers.
    """
    result = EmergencyModeService.activate(
        reason=request.reason,
        affected_districts=request.affected_districts,
        activated_by=current_user.email,
        db=db
    )
    return result

@router.post("/deactivate", dependencies=[Depends(role_required("government"))])
def deactivate_emergency(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Deactivates emergency mode and returns system to normal operations.
    """
    result = EmergencyModeService.deactivate(
        deactivated_by=current_user.email,
        db=db
    )
    return result

@router.get("/status")
def get_emergency_status():
    """
    Publicly visible endpoint to check emergency mode status.
    Used by frontend banners.
    """
    status_data = EmergencyModeService.is_active()
    return {"active": bool(status_data), "metadata": status_data}
