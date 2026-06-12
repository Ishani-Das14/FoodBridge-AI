# ==============================================================================
# FoodBridge AI - Matching Service Logic
# Implements greedy matching allocation, geo queries, and match acceptance/rejection
# ==============================================================================
import logging
import math
import re
from typing import List, Set
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import Donation, NGOProfile, Match

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes the great-circle distance between two points in meters
    using the Haversine formula.
    """
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def parse_quantity(quantity_str: str) -> int:
    """
    Parses numeric prefix from quantity string (e.g. "10 kg" -> 10).
    Defaults to 0 if parsing fails.
    """
    if not quantity_str:
        return 0
    match = re.match(r'^(\d+)', quantity_str.strip())
    if match:
        return int(match.group(1))
    try:
        return int(float(quantity_str))
    except Exception:
        logger.warning(f"Could not parse numeric quantity from '{quantity_str}'")
        return 0

def fetch_ngos_within_radius(
    db: Session,
    pickup_lat: float,
    pickup_lng: float,
    radius_meters: float,
    excluded_ngo_ids: Set[int]
) -> List[NGOProfile]:
    """
    Queries NGOs within a radius from pickup coordinates, sorting by distance.
    Uses PostGIS queries on PostgreSQL, and Haversine formula fallback on SQLite.
    """
    dialect = db.bind.dialect.name
    logger.info(f"Fetching NGOs within {radius_meters / 1000:.1f}km using {dialect} dialect.")

    if dialect == "sqlite":
        # Fallback Python calculation for SQLite in-memory testing
        all_ngos = db.query(NGOProfile).filter(NGOProfile.capacity > 0).all()
        ngo_distances = []
        for ngo in all_ngos:
            if ngo.id in excluded_ngo_ids:
                continue
            dist = haversine_distance(ngo.latitude, ngo.longitude, pickup_lat, pickup_lng)
            if dist <= radius_meters:
                ngo_distances.append((ngo, dist))
        
        # Sort by distance ascending
        ngo_distances.sort(key=lambda x: x[1])
        return [ngo for ngo, _ in ngo_distances]
    
    else:
        # Raw PostGIS query on PostgreSQL using text()
        query = text("""
            SELECT id, user_id, name, registration_number, address, latitude, longitude, capacity
            FROM ngo_profiles
            WHERE ST_DWithin(
                ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                ST_SetSRID(ST_MakePoint(:pickup_lng, :pickup_lat), 4326)::geography,
                :radius
            )
            AND capacity > 0
            ORDER BY ST_Distance(
                ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                ST_SetSRID(ST_MakePoint(:pickup_lng, :pickup_lat), 4326)::geography
            ) ASC
        """)
        
        results = db.query(NGOProfile).from_statement(query).params(
            pickup_lng=pickup_lng,
            pickup_lat=pickup_lat,
            radius=radius_meters
        ).all()
        
        # Filter excluded/rejected NGOs in Python to simplify the SQL IN parameter binding
        return [ngo for ngo in results if ngo.id not in excluded_ngo_ids]

def run_matching_for_donation(db: Session, donation_id: int) -> List[Match]:
    """
    Executes the greedy matching algorithm for a given donation.
    """
    logger.info(f"Step 1: Loading donation {donation_id}...")
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        logger.error(f"Donation {donation_id} not found.")
        return []
        
    if donation.status != "available":
        logger.warning(f"Donation {donation_id} status is '{donation.status}', returning early.")
        return []

    # Identify all NGOs that have rejected this donation
    rejected_matches = db.query(Match).filter(
        Match.donation_id == donation_id,
        Match.status == "rejected"
    ).all()
    rejected_ngo_ids = {m.ngo_id for m in rejected_matches}
    logger.info(f"Loaded rejected matches. Excluded NGO IDs: {rejected_ngo_ids}")

    remaining_qty = parse_quantity(donation.quantity)
    logger.info(f"Donation quantity parsed: {remaining_qty} units.")
    if remaining_qty <= 0:
        logger.warning(f"Quantity parsed is {remaining_qty}, nothing to allocate.")
        return []

    created_matches = []
    matched_ngo_ids = set()

    # Step 2-4: 15km matching phase
    logger.info("Executing 15km matching phase...")
    excluded_ids = rejected_ngo_ids.union(matched_ngo_ids)
    ngos_15km = fetch_ngos_within_radius(
        db, donation.pickup_lat, donation.pickup_lng, 15000, excluded_ids
    )
    logger.info(f"Found {len(ngos_15km)} eligible NGOs within 15km.")

    for ngo in ngos_15km:
        allocate = min(ngo.capacity, remaining_qty)
        if allocate <= 0:
            continue
            
        logger.info(f"Allocating {allocate} units to NGO '{ngo.name}' (ID: {ngo.id}, Capacity: {ngo.capacity})")
        match = Match(
            donation_id=donation.id,
            ngo_id=ngo.id,
            quantity_allocated=allocate,
            status="pending"
        )
        db.add(match)
        created_matches.append(match)
        matched_ngo_ids.add(ngo.id)
        
        remaining_qty -= allocate
        if remaining_qty == 0:
            logger.info("Donation fully allocated in 15km phase.")
            break

    # Step 5: 30km matching phase (if quantity remaining)
    if remaining_qty > 0:
        logger.info(f"Remaining quantity is {remaining_qty}. Extending search to 30km...")
        excluded_ids = rejected_ngo_ids.union(matched_ngo_ids)
        ngos_30km = fetch_ngos_within_radius(
            db, donation.pickup_lat, donation.pickup_lng, 30000, excluded_ids
        )
        logger.info(f"Found {len(ngos_30km)} eligible NGOs within 30km (excluding 15km matches).")
        
        for ngo in ngos_30km:
            allocate = min(ngo.capacity, remaining_qty)
            if allocate <= 0:
                continue
                
            logger.info(f"Allocating {allocate} units to NGO '{ngo.name}' (ID: {ngo.id}, Capacity: {ngo.capacity})")
            match = Match(
                donation_id=donation.id,
                ngo_id=ngo.id,
                quantity_allocated=allocate,
                status="pending"
            )
            db.add(match)
            created_matches.append(match)
            matched_ngo_ids.add(ngo.id)
            
            remaining_qty -= allocate
            if remaining_qty == 0:
                logger.info("Donation fully allocated in 30km phase.")
                break

    if remaining_qty > 0:
        logger.warning(f"Matching finished. Remaining unmatched quantity: {remaining_qty}")

    # Step 6: Update donation status
    if created_matches:
        logger.info(f"Step 6: Updating donation {donation_id} status to 'matched' (Created {len(created_matches)} matches).")
        donation.status = "matched"
        db.commit()
        
        # Step 7: Push notify_ngo Celery task
        for match in created_matches:
            db.refresh(match)
            try:
                from app.tasks.donation_tasks import notify_ngo
                notify_ngo.delay(match.id)
                logger.info(f"Step 7: Queued notify_ngo Celery task for match_id={match.id}.")
            except Exception as e:
                logger.warning(f"Step 7: Failed to queue notify_ngo Celery task: {e}")
    else:
        logger.info(f"No matches created for donation {donation_id}. Status remains 'available'.")
        db.commit()

    return created_matches

def accept_match(db: Session, match_id: int, ngo_profile_id: int) -> Match:
    """
    Enables an NGO to accept a pending match.
    Updates NGO capacity and match status.
    """
    logger.info(f"NGO profile {ngo_profile_id} accepting match {match_id}...")
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match record not found."
        )

    if match.ngo_id != ngo_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to accept this match."
        )

    if match.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match cannot be accepted because its status is '{match.status}'."
        )

    ngo = db.query(NGOProfile).filter(NGOProfile.id == ngo_profile_id).first()
    if not ngo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NGO profile not found."
        )

    if ngo.capacity < match.quantity_allocated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient capacity ({ngo.capacity}) to accept match allocation ({match.quantity_allocated})."
        )

    # Update capacity and status
    ngo.capacity -= match.quantity_allocated
    match.status = "accepted"
    db.commit()
    db.refresh(match)
    
    logger.info(f"Match {match_id} successfully accepted. NGO capacity reduced to {ngo.capacity}.")
    return match

def reject_match(db: Session, match_id: int, ngo_profile_id: int) -> Match:
    """
    Enables an NGO to reject a match.
    Clears pending matches, sets donation to available, and triggers re-matching.
    """
    logger.info(f"NGO profile {ngo_profile_id} rejecting match {match_id}...")
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match record not found."
        )

    if match.ngo_id != ngo_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to reject this match."
        )

    if match.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match cannot be rejected because its status is '{match.status}'."
        )

    # Set this match to rejected
    match.status = "rejected"
    donation_id = match.donation_id

    # Delete other pending matches for this donation to start clean
    pending_matches = db.query(Match).filter(
        Match.donation_id == donation_id,
        Match.status == "pending",
        Match.id != match_id
    ).all()
    for p_match in pending_matches:
        db.delete(p_match)

    # Reset donation status to available so it is eligible for matching again
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if donation:
        donation.status = "available"

    db.commit()
    db.refresh(match)

    logger.info(f"Match {match_id} rejected. Queueing Celery re-matching task for donation {donation_id}...")
    
    # Trigger matching task
    try:
        from app.tasks.donation_tasks import trigger_matching
        trigger_matching.delay(donation_id)
        logger.info(f"Queued trigger_matching task for donation {donation_id} after rejection.")
    except Exception as e:
        logger.warning(f"Failed to queue trigger_matching Celery task: {e}")

    return match
