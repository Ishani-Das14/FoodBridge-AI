# ==============================================================================
# FoodBridge AI - Donation Service Router
# Exposes API gateways for food posting, listing, and collection session updates
# ==============================================================================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User
from app.services.donation.schemas import DonationCreate, DonationStatusUpdate, DonationOut
from app.services.donation.service import (
    create_donation as svc_create_donation,
    list_active_donations as svc_list_active_donations,
    get_donation_by_id as svc_get_donation_by_id,
    update_donation_status as svc_update_donation_status,
    delete_donation as svc_delete_donation
)

router = APIRouter(prefix="/donations", tags=["Food Donations"])

# Separate router for restaurant-specific endpoints
restaurant_router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

@restaurant_router.get("/me/stats")
def get_my_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns dashboard stats for the logged-in restaurant."""
    from app.models import RestaurantProfile, Donation
    profile = db.query(RestaurantProfile).filter(RestaurantProfile.user_id == current_user.id).first()
    if not profile:
        return {"total_donations": 0, "meals_donated": 0, "csr_score": 0}
    donations = db.query(Donation).filter(Donation.restaurant_id == profile.id).all()
    total = len(donations)
    delivered = [d for d in donations if d.status == "delivered"]
    meals = sum(int(d.quantity) if str(d.quantity).isdigit() else 0 for d in delivered)
    csr = min(100, round(meals * 0.5))
    return {"total_donations": total, "meals_donated": meals, "csr_score": csr}

@router.get("/my", response_model=List[DonationOut])
def get_my_donations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns all donations created by the logged-in restaurant."""
    from app.models import RestaurantProfile, Donation
    profile = db.query(RestaurantProfile).filter(RestaurantProfile.user_id == current_user.id).first()
    if not profile:
        return []
    return db.query(Donation).filter(Donation.restaurant_id == profile.id).order_by(Donation.created_at.desc()).all()

@router.post("", response_model=DonationOut, status_code=status.HTTP_201_CREATED)
def create_donation(
    data: DonationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new food donation post.
    Enforces Restaurant-only clearance via the service layer.
    Schedules matching algorithm runs.
    """
    return svc_create_donation(db, current_user, data)

@router.get("", response_model=List[DonationOut])
def list_active_donations(
    status: str = "available",
    city: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Lists active/available donation posts, paginated.
    Optional query filtering by city (checking pickup_address).
    """
    return svc_list_active_donations(db, status, city, limit, offset)

@router.get("/{donation_id}", response_model=DonationOut)
def get_donation(
    donation_id: int,
    db: Session = Depends(get_db)
):
    """Retrieves detailed information of a single donation post by ID."""
    return svc_get_donation_by_id(db, donation_id)

@router.patch("/{donation_id}/status", response_model=DonationOut)
def update_status(
    donation_id: int,
    payload: DonationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates the progress status of a donation post (picked_up, delivered, expired).
    Enforces Role-Based Access Control policies:
    - Volunteer -> 'picked_up'
    - NGO -> 'delivered'
    - Restaurant / Admin -> 'expired'
    """
    return svc_update_donation_status(db, current_user, donation_id, payload.status)

@router.delete("/{donation_id}", response_model=DonationOut)
def delete_donation(
    donation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soft-deletes a food donation post (setting status to 'expired').
    Enforces that only the restaurant owner who created the post can delete it.
    """
    return svc_delete_donation(db, current_user, donation_id)
