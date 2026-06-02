# ==============================================================================
# FoodBridge AI - Donation Service Operations
# Manages SQL transactions and business logic for food redistribution posts
# ==============================================================================
import datetime
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import User, RestaurantProfile, Donation
from app.services.donation.schemas import DonationCreate
from app.tasks.donation_tasks import trigger_matching

logger = logging.getLogger(__name__)

def create_donation(db: Session, user: User, data: DonationCreate) -> Donation:
    """
    Creates a new food donation post.
    Enforces that only Restaurant accounts can post.
    Schedules background pairings via Celery.
    """
    if user.role != "restaurant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only Restaurant accounts can create donation posts."
        )

    # Resolve restaurant profile
    restaurant = db.query(RestaurantProfile).filter(RestaurantProfile.user_id == user.id).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant profile not found for authenticated user."
        )

    # Compute server-side expiry timestamp
    expiry_time = data.prep_time + datetime.timedelta(minutes=data.expiry_minutes)

    donation = Donation(
        restaurant_id=restaurant.id,
        food_type=data.food_type,
        quantity=data.quantity,
        prep_time=data.prep_time,
        expiry_time=expiry_time,
        pickup_address=data.pickup_address,
        pickup_lat=data.pickup_lat,
        pickup_lng=data.pickup_lng,
        status="available"
    )

    db.add(donation)
    db.commit()
    db.refresh(donation)

    # Queue Celery task with a 2-minute delay
    try:
        trigger_matching.apply_async(args=[donation.id], countdown=120)
        logger.info(f"Queued trigger_matching task for donation {donation.id} with 2-minute delay.")
    except Exception as e:
        logger.warning(f"Failed to queue Celery matching task: {e} (Redis/Celery offline?)")

    return donation

def list_active_donations(
    db: Session,
    status_filter: str = "available",
    city: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Donation]:
    """Queries active/available donation posts, with optional city filtering."""
    query = db.query(Donation).filter(Donation.status == status_filter)

    if city:
        query = query.filter(Donation.pickup_address.ilike(f"%{city}%"))

    return query.offset(offset).limit(limit).all()

def get_donation_by_id(db: Session, donation_id: int) -> Donation:
    """Retrieves a single donation post by ID. Raises 404 if missing."""
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation post not found."
        )
    return donation

def update_donation_status(db: Session, user: User, donation_id: int, new_status: str) -> Donation:
    """
    Updates the status of a donation post.
    Enforces strict role permissions:
    - Volunteers can set 'picked_up'
    - NGOs can set 'delivered'
    - Systems/Admins/Owners can set 'expired'
    """
    donation = get_donation_by_id(db, donation_id)

    # Role check validation
    if new_status == "picked_up":
        if user.role != "volunteer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only Volunteer accounts can mark a donation as picked up."
            )
    elif new_status == "delivered":
        if user.role != "ngo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only NGO accounts can mark a donation as delivered."
            )
    elif new_status == "expired":
        # Allow the owner restaurant or admins to expire manually
        restaurant = db.query(RestaurantProfile).filter(RestaurantProfile.user_id == user.id).first()
        is_owner = restaurant and donation.restaurant_id == restaurant.id
        if user.role != "government" and not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only the posting Restaurant or an Administrator can expire this donation."
            )

    donation.status = new_status
    db.commit()
    db.refresh(donation)
    return donation

def delete_donation(db: Session, user: User, donation_id: int) -> Donation:
    """
    Soft-deletes a food donation post (setting status to 'expired').
    Enforces that only the restaurant owner who created the post can delete it.
    """
    donation = get_donation_by_id(db, donation_id)

    # Enforce Restaurant role
    if user.role != "restaurant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only the posting Restaurant can delete this donation."
        )

    # Retrieve caller's Restaurant Profile
    restaurant = db.query(RestaurantProfile).filter(RestaurantProfile.user_id == user.id).first()
    if not restaurant or donation.restaurant_id != restaurant.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not own the restaurant profile associated with this donation."
        )

    # Soft delete: change status to expired
    donation.status = "expired"
    db.commit()
    db.refresh(donation)
    return donation
