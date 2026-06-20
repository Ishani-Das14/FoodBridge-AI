import os
import sys
import json
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(project_root)

from app.core.database import get_db
from app.core.redis import redis_client
from app.models import RestaurantProfile, Donation
from app.services.csr.calculator import CSRCalculator
import boto3
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

router = APIRouter(prefix="/restaurants", tags=["CSR and Leaderboard"])
logger = logging.getLogger(__name__)

# Also add the leaderboard endpoint here, as per instructions.
leaderboard_router = APIRouter(prefix="/leaderboard", tags=["Public Leaderboard"])

@router.get("/{id}/csr-score")
def get_csr_score(id: int, db: Session = Depends(get_db)):
    """
    Returns full CSR score breakdown. Caches in Redis for 1 hour.
    """
    cache_key = f"csr_score:{id}"
    
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    restaurant = db.query(RestaurantProfile).filter(RestaurantProfile.id == id).first()
    if not restaurant:
        # Fallback to user id check
        restaurant = db.query(RestaurantProfile).filter(RestaurantProfile.user_id == id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant profile not found")
        id = restaurant.id
            
    calculator = CSRCalculator()
    score_data = calculator.calculate_score(id, db)
    
    if redis_client:
        try:
            redis_client.setex(cache_key, 3600, json.dumps(score_data))
        except Exception:
            pass
            
    return score_data

@router.get("/{id}/certificate")
def generate_csr_certificate(id: int, month: str, db: Session = Depends(get_db)):
    """
    Generates monthly donation certificate PDF. month format: YYYY-MM
    """
    restaurant = db.query(RestaurantProfile).filter(RestaurantProfile.user_id == id).first()
    if not restaurant:
        restaurant = db.query(RestaurantProfile).filter(RestaurantProfile.id == id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant profile not found")
            
    # Calculate stats for that month
    try:
        year_str, month_str = month.split('-')
        target_year = int(year_str)
        target_month = int(month_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
        
    donations = db.query(Donation).filter(
        Donation.restaurant_id == restaurant.id,
        Donation.status == 'delivered',
        func.extract('year', Donation.created_at) == target_year,
        func.extract('month', Donation.created_at) == target_month
    ).all()
    
    total_meals = sum(int(d.quantity) if str(d.quantity).isdigit() else 1 for d in donations)
    kg_saved = total_meals * 0.4
    co2_saved = kg_saved * 2.5
    
    # Generate PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 80, "FoodBridge AI - Official Tax Certificate")
    c.setStrokeColor(colors.gold)
    c.setLineWidth(3)
    c.rect(20, 20, width - 40, height - 40)
    
    c.setFont("Helvetica", 14)
    c.drawString(50, height - 140, f"Issued to: {restaurant.name}")
    c.drawString(50, height - 170, f"Period: {month}")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 230, "Monthly Impact Summary:")
    c.setFont("Helvetica", 14)
    c.drawString(50, height - 260, f"Total Meals Donated: {total_meals}")
    c.drawString(50, height - 290, f"Kg of Food Saved: {kg_saved:.2f} kg")
    c.drawString(50, height - 320, f"Equivalent CO2 Emissions Prevented: {co2_saved:.2f} kg")
    
    cert_id = str(uuid.uuid4())
    c.setFont("Courier", 10)
    c.drawString(50, height - 400, f"Certificate ID: {cert_id}")
    
    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Upload to S3
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME", "foodbridge-certificates")
    object_name = f"certificates/monthly/{restaurant.id}_{month}.pdf"
    
    url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
    if os.getenv("AWS_ACCESS_KEY_ID"):
        s3 = boto3.client('s3', aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"), region_name=os.getenv("AWS_REGION", "ap-south-1"))
        try:
            s3.put_object(Bucket=bucket_name, Key=object_name, Body=pdf_bytes, ContentType='application/pdf', ACL='public-read')
        except Exception as e:
            logger.error(f"S3 Upload failed: {e}")
            url = "s3-upload-failed"
            
    return {"certificate_url": url}

@leaderboard_router.get("/restaurants")
def get_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    cache_key = f"csr_leaderboard:{limit}"
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass
            
    # Calculate CSR roughly for leaderboard (we just use precalculated top logic for speed, or re-run)
    # Since we need badge, total_meals, city, we can just aggregate total_meals and derive badge
    results = db.query(
        RestaurantProfile.id,
        RestaurantProfile.name,
        RestaurantProfile.address,
        func.sum(func.cast(Donation.quantity, db.Integer)).label("total_meals")
    ).join(Donation, Donation.restaurant_id == RestaurantProfile.id)\
     .filter(Donation.status == 'delivered')\
     .group_by(RestaurantProfile.id)\
     .order_by(desc("total_meals"))\
     .limit(limit).all()
     
    data = []
    calculator = CSRCalculator()
    for r in results:
        # Full recalculate is slow for leaderboard, but requested logic implies we just need score.
        # Calling calculate_score handles it properly.
        score_data = calculator.calculate_score(r.id, db)
        city = r.address.split(",")[-1].strip() if r.address else "Unknown"
        data.append({
            "restaurant_id": r.id,
            "name": r.name,
            "city": city,
            "badge": score_data["badge"],
            "total_meals": score_data["total_meals"],
            "score": score_data["score"]
        })
        
    if redis_client:
        try:
            redis_client.setex(cache_key, 600, json.dumps(data))
        except Exception:
            pass
            
    return data
