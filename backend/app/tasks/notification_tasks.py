import os
import json
import logging
from celery import shared_task
from pywebpush import webpush, WebPushException
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import Notification, NGOProfile, VolunteerProfile, RestaurantProfile, Donation, User
from app.auth.service import redis_client

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS = {"sub": f"mailto:{os.getenv('VAPID_CLAIM_EMAIL', 'admin@foodbridge.ai')}"}
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@foodbridge.ai")

def get_subscription_info(user_id: int):
    """Retrieve push subscription from Redis."""
    if not redis_client:
        return None
    sub_json = redis_client.get(f"push_sub:{user_id}")
    return json.loads(sub_json) if sub_json else None

def send_web_push(subscription_info: dict, title: str, body: str):
    """Send web push notification using pywebpush."""
    if not subscription_info or not VAPID_PRIVATE_KEY:
        logger.warning("No subscription info or VAPID keys available. Skipping push.")
        return
    try:
        payload = json.dumps({"title": title, "body": body})
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
    except WebPushException as e:
        logger.error(f"Web push failed: {e}")
        # Not raising to prevent task from failing if push fails
    except Exception as e:
        logger.error(f"Error in web push: {e}")

def send_email(to_email: str, subject: str, body: str):
    """Send email using SendGrid."""
    if not SENDGRID_API_KEY:
        logger.warning("SendGrid API key not set. Skipping email.")
        return
    try:
        message = Mail(
            from_email=SENDGRID_FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        logger.error(f"SendGrid email failed: {e}")

def create_in_app_notification(db, user_id: int, title: str, body: str):
    notification = Notification(user_id=user_id, title=title, body=body)
    db.add(notification)
    db.commit()

@shared_task(max_retries=3, countdown=5)
def notify_ngo_new_donation(ngo_id: int, donation_id: int):
    with SessionLocal() as db:
        ngo = db.query(NGOProfile).filter(NGOProfile.id == ngo_id).first()
        donation = db.query(Donation).filter(Donation.id == donation_id).first()
        
        if not ngo or not donation:
            logger.error("NGO or Donation not found for notification.")
            return

        user_id = ngo.user_id
        email = ngo.user.email
        title = "New Donation Available"
        body = f"New donation available near you: {donation.food_type} x{donation.quantity} packs"

        # 1. In-App Notification
        create_in_app_notification(db, user_id, title, body)

        # 2. Web Push
        sub_info = get_subscription_info(user_id)
        if sub_info:
            send_web_push(sub_info, title, body)
        else:
            logger.warning(f"No push subscription found for NGO user {user_id}")

        # 3. Email
        send_email(email, "Food available near you", f"Hello {ngo.name},\n\n{body}\n\nLogin to accept it.")

@shared_task(max_retries=3, countdown=5)
def notify_volunteer_assigned(volunteer_id: int, delivery_id: int): # In our schema, delivery is usually match or implicit. Using donation/match for context
    with SessionLocal() as db:
        # delivery_id could map to a match or donation depending on schema. We'll use match or donation.
        # Since I don't have the full delivery schema, I'll assume we can fetch the donation or match
        # If it's donation ID:
        volunteer = db.query(VolunteerProfile).filter(VolunteerProfile.id == volunteer_id).first()
        # For simplicity, assuming delivery_id is donation_id here based on earlier steps
        donation = db.query(Donation).filter(Donation.id == delivery_id).first()
        
        if not volunteer or not donation:
            logger.error("Volunteer or Delivery not found.")
            return

        user_id = volunteer.user_id
        restaurant_name = donation.restaurant_name
        ngo_name = donation.matches[0].ngo.name if donation.matches else "NGO"
        
        title = "Pickup Assigned"
        body = f"You have a new pickup: {restaurant_name} → {ngo_name}. Pickup at {donation.pickup_address}."

        create_in_app_notification(db, user_id, title, body)

        sub_info = get_subscription_info(user_id)
        if sub_info:
            send_web_push(sub_info, title, body)
        else:
            logger.warning(f"No push subscription for volunteer user {user_id}")

@shared_task(max_retries=3, countdown=5)
def notify_restaurant_delivered(restaurant_id: int, donation_id: int, meals_count: int):
    with SessionLocal() as db:
        restaurant = db.query(RestaurantProfile).filter(RestaurantProfile.id == restaurant_id).first()
        
        if not restaurant:
            return

        user_id = restaurant.user_id
        email = restaurant.user.email
        title = "Delivery Completed!"
        body = f"Your donation was delivered! {meals_count} meals served."

        create_in_app_notification(db, user_id, title, body)

        sub_info = get_subscription_info(user_id)
        if sub_info:
            send_web_push(sub_info, title, body)

        # Email Certificate Summary
        send_email(
            email, 
            "Donation Delivered - Certificate Summary", 
            f"Thank you {restaurant.name}!\n\nYour recent donation helped serve {meals_count} meals. View your CSR dashboard for the updated certificate."
        )

@shared_task(max_retries=3, countdown=5)
def notify_ngo_volunteer_coming(ngo_id: int, volunteer_name: str, eta_minutes: int):
    with SessionLocal() as db:
        ngo = db.query(NGOProfile).filter(NGOProfile.id == ngo_id).first()
        
        if not ngo:
            return

        user_id = ngo.user_id
        title = "Volunteer En Route"
        body = f"Volunteer {volunteer_name} is on the way. ETA: {eta_minutes} min"

        create_in_app_notification(db, user_id, title, body)

        sub_info = get_subscription_info(user_id)
        if sub_info:
            send_web_push(sub_info, title, body)
