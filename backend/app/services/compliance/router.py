import os
import sys
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(project_root)

from app.core.database import get_db
from app.models import Donation, Match, RestaurantProfile, NGOProfile
from app.services.compliance.validator import FSSAIValidator
from app.services.compliance.certificate import CertificateGenerator

router = APIRouter(prefix="/compliance", tags=["Food Safety Compliance"])

class ValidationRequest(BaseModel):
    food_type: str
    prep_time: datetime
    expiry_minutes: int

@router.post("/validate")
def validate_donation(request: ValidationRequest):
    """
    Validates if a donation meets FSSAI safety windows.
    Returns 200 if valid, else raises 400.
    """
    validator = FSSAIValidator()
    result = validator.validate_donation_safety(
        food_type=request.food_type,
        prep_time=request.prep_time,
        expiry_minutes=request.expiry_minutes
    )
    if not result["is_compliant"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["reason"])
    
    return result

@router.get("/certificate/{delivery_id}")
def generate_certificate(delivery_id: str, db: Session = Depends(get_db)):
    """
    Generates PDF certificate, uploads to S3, returns {certificate_url}.
    Only callable after delivery.status == 'delivered'.
    """
    # Assuming delivery_id maps to Match.id
    match = db.query(Match).filter(Match.id == delivery_id).first()
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery record not found.")
        
    if match.status != "delivered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Certificate can only be generated for 'delivered' status. Current: {match.status}"
        )
        
    donation = db.query(Donation).filter(Donation.id == match.donation_id).first()
    restaurant = db.query(RestaurantProfile).filter(RestaurantProfile.id == donation.restaurant_id).first()
    ngo = db.query(NGOProfile).filter(NGOProfile.id == match.ngo_id).first()
    
    cert_gen = CertificateGenerator()
    pdf_bytes = cert_gen.generate_safety_certificate(delivery_id, donation, restaurant, ngo)
    url = cert_gen.upload_to_s3(pdf_bytes, delivery_id)
    
    return {"certificate_url": url}
