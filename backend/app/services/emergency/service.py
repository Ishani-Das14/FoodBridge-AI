import os
import sys
import json
from datetime import datetime
from sqlalchemy.orm import Session

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(project_root)

from app.core.redis import redis_client
from app.models import EmergencyLog
from app.tasks.notification_tasks import broadcast_emergency_notification

class EmergencyModeService:
    REDIS_KEY = "emergency_mode:active"

    @classmethod
    def activate(cls, reason: str, affected_districts: list[str], activated_by: str, db: Session) -> dict:
        metadata = {
            "reason": reason,
            "affected_districts": affected_districts,
            "activated_by": activated_by,
            "activated_at": datetime.utcnow().isoformat()
        }
        
        if redis_client:
            redis_client.set(cls.REDIS_KEY, json.dumps(metadata))
            
        # Log to PostgreSQL
        log_entry = EmergencyLog(
            action="activate",
            reason=reason,
            affected_districts=affected_districts,
            triggered_by=activated_by
        )
        db.add(log_entry)
        db.commit()
        
        # Trigger Celery task to ALL volunteers
        message = f"EMERGENCY MODE ACTIVE: {reason}. Expect priority pickup requests."
        broadcast_emergency_notification.delay(message)
        
        return {"status": "activated", "metadata": metadata}

    @classmethod
    def deactivate(cls, deactivated_by: str, db: Session) -> dict:
        if redis_client:
            redis_client.delete(cls.REDIS_KEY)
            
        log_entry = EmergencyLog(
            action="deactivate",
            triggered_by=deactivated_by
        )
        db.add(log_entry)
        db.commit()
        
        return {"status": "deactivated"}

    @classmethod
    def is_active(cls) -> dict | None:
        if redis_client:
            try:
                data = redis_client.get(cls.REDIS_KEY)
                if data:
                    return json.loads(data)
            except Exception:
                pass
        return None

    @classmethod
    def get_emergency_matching_radius(cls) -> float:
        if cls.is_active():
            return 50.0  # 50km
        return 15.0  # Default 15km

    @classmethod
    def get_expiry_grace_period(cls) -> int:
        if cls.is_active():
            return 120  # minutes
        return 0
