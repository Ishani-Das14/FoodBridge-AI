import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.auth.router import get_current_user
from app.models import User
from app.services.notifications import service, schemas

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

# VAPID Public Key for frontend
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")

@router.get("/vapid-public-key")
def get_vapid_public_key():
    return {"vapid_public_key": VAPID_PUBLIC_KEY}

@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe_to_push(
    subscription: schemas.PushSubscription,
    current_user: User = Depends(get_current_user)
):
    # The frontend sends the PushSubscription object directly
    # We wrap it in our payload format for the service
    payload = schemas.SubscriptionPayload(subscription=subscription)
    success = service.save_push_subscription(current_user.id, payload)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save subscription")
    return {"message": "Successfully subscribed to push notifications"}

@router.get("", response_model=List[schemas.NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return service.get_unread_notifications(db, current_user.id)

@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = service.mark_as_read(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}
