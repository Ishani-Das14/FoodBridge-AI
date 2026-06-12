# ==============================================================================
# FoodBridge AI - Matching Service Router
# Exposes API gateways for match triggering, retrieval, and status updates
# ==============================================================================
import os
from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user, role_required
from app.models import User, Match
from app.services.matching.schemas import MatchOut
from app.services.matching.service import (
    run_matching_for_donation,
    accept_match,
    reject_match
)

router = APIRouter(prefix="/match", tags=["NGO Matching"])

# Internal API key validation for Celery/System-only access
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "super_secret_internal_key_999")

async def verify_internal_auth(
    x_internal_token: str = Header(None, alias="X-Internal-Token")
):
    """
    Validates that the request has a valid X-Internal-Token header.
    Restricts access to system-level/Celery-level processes.
    """
    if not x_internal_token or x_internal_token != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied: Internal system authentication required."
        )

@router.post("/{donation_id}", response_model=List[MatchOut], status_code=status.HTTP_201_CREATED)
def trigger_matching(
    donation_id: int,
    db: Session = Depends(get_db),
    _internal: None = Depends(verify_internal_auth)
):
    """
    Triggers the NGO matching algorithm for a food donation.
    Authorized for internal Celery background processes only.
    """
    return run_matching_for_donation(db, donation_id)

@router.get("/donation/{donation_id}", response_model=List[MatchOut])
def get_donation_matches(
    donation_id: int,
    db: Session = Depends(get_db)
):
    """Retrieves all match records generated for a specific donation."""
    return db.query(Match).filter(Match.donation_id == donation_id).all()

@router.patch("/{match_id}/accept", response_model=MatchOut)
def accept_donation_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("ngo"))
):
    """
    NGO accepts the matched donation allocation.
    Updates NGO capacity and match status.
    """
    ngo_profile = current_user.ngo_profile
    if not ngo_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated user does not have an NGO profile."
        )
    return accept_match(db, match_id, ngo_profile.id)

@router.patch("/{match_id}/reject", response_model=MatchOut)
def reject_donation_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("ngo"))
):
    """
    NGO rejects the matched donation allocation.
    Resets the donation state and schedules a new background matching sweep.
    """
    ngo_profile = current_user.ngo_profile
    if not ngo_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated user does not have an NGO profile."
        )
    return reject_match(db, match_id, ngo_profile.id)
