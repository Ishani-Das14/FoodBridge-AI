# ==============================================================================
# FoodBridge AI - Donation Service Background Tasks
# Implements matching simulation triggers and cleanups for expired donations
# ==============================================================================
import datetime
import logging
from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import Donation

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.donation_tasks.trigger_matching")
def trigger_matching(donation_id: int) -> str:
    """
    Background worker task triggered 2 minutes after a donation is posted.
    Orchestrates matching calculations between restaurants and active NGOs.
    """
    logger.info(f"Triggering matching matching service for donation_id={donation_id}...")
    # Simulate routing solver / charity pairing calculation
    return f"Orchestrated match search successfully completed for donation {donation_id}."

@celery_app.task(name="app.tasks.donation_tasks.expire_donations")
def expire_donations() -> str:
    """
    Periodic cron/beat sweep that identifies open, uncollected donations
    that have surpassed their computed expiry timestamp, setting them to 'expired'.
    """
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()
        logger.info(f"Running sweep to check for expired donations past {now}...")
        
        # Select all available donations whose expiry time is in the past
        expired_donations = db.query(Donation).filter(
            Donation.status == "available",
            Donation.expiry_time < now
        ).all()
        
        count = len(expired_donations)
        for donation in expired_donations:
            donation.status = "expired"
        
        if count > 0:
            db.commit()
            logger.info(f"Successfully marked {count} donations as expired.")
        else:
            logger.info("No expired donations found during this sweep.")
            
        return f"Expired {count} donations."
    except Exception as e:
        logger.error(f"Failed to execute expiration sweep: {e}")
        db.rollback()
        raise e
    finally:
        db.close()
