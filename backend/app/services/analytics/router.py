import os
import sys
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(project_root)

from app.core.database import get_db
from app.models import Donation, RestaurantProfile, NGOProfile, Match
from app.core.redis import redis_client

router = APIRouter(prefix="/analytics", tags=["Government Analytics"])

@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    today = date.today()
    
    # 1. Total donations today
    total_donations_today = db.query(Donation).filter(func.date(Donation.created_at) == today).count()
    
    # 2. Total meals saved today (status=delivered or matched/picked_up)
    # Assuming delivered, picked_up, matched count as "saved" for now, or just focus on non-expired non-available.
    # Let's sum quantity for status in ['matched', 'picked_up', 'delivered']
    meals_saved_today = db.query(func.sum(Donation.quantity)).filter(
        func.date(Donation.created_at) == today,
        Donation.status.in_(["matched", "picked_up", "delivered"])
    ).scalar() or 0
    
    total_kg_saved_today = meals_saved_today * 0.4
    
    # 3. Active donations now
    active_donations_now = db.query(Donation).filter(Donation.status == "available").count()
    
    # 4. Expired donations today
    expired_donations_today = db.query(Donation).filter(
        func.date(Donation.created_at) == today,
        Donation.status == "expired"
    ).count()
    
    # 5. Top donating restaurant today
    # Join with RestaurantProfile
    top_rest = db.query(
        RestaurantProfile.restaurant_name,
        func.sum(Donation.quantity).label('total_meals')
    ).join(Donation, Donation.restaurant_id == RestaurantProfile.user_id)\
     .filter(func.date(Donation.created_at) == today)\
     .group_by(RestaurantProfile.restaurant_name)\
     .order_by(desc('total_meals')).first()
     
    top_restaurant_data = None
    if top_rest:
        top_restaurant_data = {"name": top_rest.restaurant_name, "meals_today": top_rest.total_meals}

    return {
        "total_donations_today": total_donations_today,
        "total_meals_saved_today": float(meals_saved_today),
        "total_kg_saved_today": float(total_kg_saved_today),
        "active_donations_now": active_donations_now,
        "expired_donations_today": expired_donations_today,
        "top_donating_restaurant": top_restaurant_data
    }

@router.get("/waste-trend")
def get_waste_trend(days: int = 30, db: Session = Depends(get_db)):
    cutoff_date = date.today() - timedelta(days=days)
    
    # Group by DATE(created_at)
    # Sum quantity if status in (matched, picked_up, delivered)
    # Count donations
    results = db.query(
        func.date(Donation.created_at).label("date"),
        func.sum(case((Donation.status.in_(["matched", "picked_up", "delivered"]), Donation.quantity), else_=0)).label("meals_saved"),
        func.count(Donation.id).label("donations_count")
    ).filter(
        func.date(Donation.created_at) >= cutoff_date
    ).group_by(
        func.date(Donation.created_at)
    ).order_by(
        func.date(Donation.created_at)
    ).all()
    
    data = []
    for r in results:
        meals = float(r.meals_saved or 0)
        data.append({
            "date": str(r.date),
            "meals_saved": meals,
            "kg_saved": meals * 0.4,
            "donations_count": r.donations_count
        })
    return data

@router.get("/ngo-gap")
def get_ngo_gap(db: Session = Depends(get_db)):
    """Join forecasts from redis with actual deliveries today."""
    today_str = str(date.today())
    
    # Load forecasts from redis
    forecast_key = f"forecast:{today_str}"
    forecasts = []
    if redis_client:
        try:
            cached = redis_client.get(forecast_key)
            if cached:
                forecasts = json.loads(cached)
        except Exception:
            pass
            
    # Load actual deliveries today per NGO
    # We will sum match quantities where status is 'delivered'
    deliveries = db.query(
        Match.ngo_id,
        func.sum(Match.quantity_allocated).label("actual_received")
    ).filter(
        func.date(Match.created_at) == date.today(),
        Match.status == "delivered"
    ).group_by(Match.ngo_id).all()
    
    actual_map = {str(d.ngo_id): float(d.actual_received or 0) for d in deliveries}
    
    # Get all NGOs to map names
    ngos = db.query(NGOProfile).all()
    ngo_names = {str(n.id): n.organization_name for n in ngos}
    
    result = []
    # If no forecasts found in redis, we just return empty or partial
    for f in forecasts:
        ngo_id = f["ngo_id"]
        predicted = f["predicted_meals"]
        actual = actual_map.get(ngo_id, 0.0)
        gap = predicted - actual
        
        result.append({
            "ngo_id": ngo_id,
            "ngo_name": ngo_names.get(ngo_id, f"NGO {ngo_id}"),
            "predicted_need": predicted,
            "actual_received": actual,
            "gap": gap,
            "lower_bound": f.get("lower_bound", 0),
            "upper_bound": f.get("upper_bound", 0)
        })
        
    return result

@router.get("/donation-funnel")
def get_donation_funnel(db: Session = Depends(get_db)):
    today = date.today()
    results = db.query(
        Donation.status,
        func.count(Donation.id).label("count")
    ).filter(
        func.date(Donation.created_at) == today
    ).group_by(Donation.status).all()
    
    status_counts = {r.status: r.count for r in results}
    
    return {
        "available": status_counts.get("available", 0),
        "matched": status_counts.get("matched", 0),
        "picked_up": status_counts.get("picked_up", 0),
        "delivered": status_counts.get("delivered", 0),
        "expired": status_counts.get("expired", 0)
    }

@router.get("/top-restaurants")
def get_top_restaurants(limit: int = 10, db: Session = Depends(get_db)):
    results = db.query(
        RestaurantProfile.restaurant_name,
        RestaurantProfile.address,
        func.sum(Donation.quantity).label("total_meals")
    ).join(Donation, Donation.restaurant_id == RestaurantProfile.user_id)\
     .filter(Donation.status.in_(["matched", "picked_up", "delivered"]))\
     .group_by(RestaurantProfile.restaurant_name, RestaurantProfile.address)\
     .order_by(desc("total_meals"))\
     .limit(limit).all()
     
    data = []
    for idx, r in enumerate(results):
        meals = float(r.total_meals or 0)
        if meals > 500:
            badge = "Gold"
        elif meals > 200:
            badge = "Silver"
        elif meals > 0:
            badge = "Bronze"
        else:
            badge = "None"
            
        # Try to parse city from address if possible, else just use address
        city = r.address.split(",")[-1].strip() if r.address else "Unknown"
        
        data.append({
            "rank": idx + 1,
            "restaurant_name": r.restaurant_name,
            "city": city,
            "total_meals": meals,
            "badge": badge
        })
    return data
