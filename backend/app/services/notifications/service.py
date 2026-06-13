import json
import logging
from sqlalchemy.orm import Session
from app.models import Notification
from app.auth.service import redis_client
from app.services.notifications.schemas import SubscriptionPayload

logger = logging.getLogger(__name__)

def save_push_subscription(user_id: int, payload: SubscriptionPayload) -> bool:
    """Save the web push subscription object to Redis."""
    if redis_client is None:
        logger.warning("Redis is not available. Cannot save push subscription.")
        return False
    
    key = f"push_sub:{user_id}"
    try:
        # Convert subscription object to JSON string
        sub_json = payload.subscription.model_dump_json()
        # No expiration for subscription, or set a long TTL
        redis_client.set(key, sub_json)
        return True
    except Exception as e:
        logger.error(f"Failed to save push subscription to Redis for user {user_id}: {e}")
        return False

def get_push_subscription(user_id: int) -> dict | None:
    """Retrieve the web push subscription from Redis."""
    if redis_client is None:
        return None
    try:
        sub_json = redis_client.get(f"push_sub:{user_id}")
        if sub_json:
            return json.loads(sub_json)
        return None
    except Exception as e:
        logger.error(f"Failed to get push subscription from Redis for user {user_id}: {e}")
        return None

def get_unread_notifications(db: Session, user_id: int):
    """Retrieve unread notifications for a user."""
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).order_by(Notification.created_at.desc()).all()

def mark_as_read(db: Session, notification_id: int, user_id: int) -> bool:
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if notification:
        notification.is_read = True
        db.commit()
        return True
    return False
