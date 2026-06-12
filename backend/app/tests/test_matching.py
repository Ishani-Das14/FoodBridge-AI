# ==============================================================================
# FoodBridge AI - Matching Service Test Suite
# Tests matching allocation logic, FastAPI matching routes, token access, and actions
# ==============================================================================
import datetime
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.auth.dependencies import get_current_user
from app.auth.router import router as auth_router
from app.services.matching.router import router as matching_router
from app.services.donation.router import router as donation_router
from app.models import Donation, NGOProfile, Match, User
from app.tasks.celery_app import celery_app
import app.tasks.donation_tasks as donation_tasks

# Force Celery to execute tasks synchronously for test purposes
celery_app.conf.task_always_eager = True

# ------------------------------------------------------------------------------
# 1. In-Memory SQLite Database Setup for Tests
# ------------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock SessionLocal for Celery tasks running in testing environment
donation_tasks.SessionLocal = TestingSessionLocal

# ------------------------------------------------------------------------------
# 2. Test App Initialization & Router Mounting
# ------------------------------------------------------------------------------
app = FastAPI()
app.dependency_overrides[get_db] = override_get_db
app.include_router(auth_router, prefix="/api/v1")
app.include_router(donation_router, prefix="/api/v1")
app.include_router(matching_router, prefix="/api/v1")

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Initializes schema before every test and drops it afterward."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# Helper function to register and acquire access tokens for different roles
def register_and_login_user(email: str, role: str, name: str, lat: float = 40.7128, lng: float = -74.0060, capacity: int = 10) -> str:
    # 1. Register base account
    if role == "restaurant":
        client.post(
            "/api/v1/auth/register/restaurant",
            json={
                "email": email,
                "password": "securepassword123",
                "name": name,
                "address": "123 Gourmet Ave, Cityville",
                "latitude": lat,
                "longitude": lng
            }
        )
    elif role == "ngo":
        client.post(
            "/api/v1/auth/register/ngo",
            json={
                "email": email,
                "password": "charitypassword123",
                "name": name,
                "registration_number": f"REG-{email.split('@')[0]}",
                "address": "456 Charity Lane, Cityville",
                "latitude": lat,
                "longitude": lng,
                "capacity": capacity
            }
        )
    elif role == "volunteer":
        client.post(
            "/api/v1/auth/register/volunteer",
            json={
                "email": email,
                "password": "volunteerpassword123",
                "name": name,
                "phone_number": "+15550001",
                "vehicle_type": "car"
            }
        )
        
    # 2. Login
    pwd = "securepassword123" if role == "restaurant" else ("charitypassword123" if role == "ngo" else "volunteerpassword123")
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": pwd}
    )
    return res.json()["access_token"]

# ------------------------------------------------------------------------------
# 3. Test Cases
# ------------------------------------------------------------------------------

def test_internal_matching_endpoint_security():
    """Verifies that POST /match/{donation_id} enforces the internal API key."""
    # Try calling without header -> 401
    res = client.post("/api/v1/match/1")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Try calling with incorrect header -> 401
    res = client.post("/api/v1/match/1", headers={"X-Internal-Token": "wrong_key"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Try calling with correct header -> 201 (returns empty list since donation doesn't exist, but auth succeeds)
    res = client.post("/api/v1/match/999", headers={"X-Internal-Token": "super_secret_internal_key_999"})
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json() == []

def test_greedy_allocation_within_radii():
    """
    Verifies that donations are correctly distributed based on NGO distance and capacity.
    - NGO A: 5km away, capacity = 10
    - NGO B: 20km away, capacity = 10
    - NGO C: 50km away, capacity = 100
    - Donation quantity: 15 units
    Should match NGO A (10 units) and NGO B (5 units). NGO C is too far.
    """
    # 1. Register restaurant and create donation
    rest_token = register_and_login_user("nyc-restaurant@foodbridge.org", "restaurant", "Central Cafe", lat=40.7128, lng=-74.0060)
    
    donation_res = client.post(
        "/api/v1/donations",
        json={
            "food_type": "Hot Meals",
            "quantity": "15 meals",
            "prep_time": datetime.datetime.utcnow().isoformat(),
            "expiry_minutes": 120,
            "pickup_address": "Central Cafe, NYC",
            "pickup_lat": 40.7128,
            "pickup_lng": -74.0060
        },
        headers={"Authorization": f"Bearer {rest_token}"}
    )
    assert donation_res.status_code == status.HTTP_201_CREATED
    donation_id = donation_res.json()["id"]

    # 2. Register NGOs at different distances
    # NGO A: ~8km away (40.7306, -73.9352) -> within 15km
    register_and_login_user("ngo-a@foodbridge.org", "ngo", "NGO A", lat=40.7306, lng=-73.9352, capacity=10)
    
    # NGO B: ~22km away (40.8500, -73.8500) -> within 30km (outside 15km)
    register_and_login_user("ngo-b@foodbridge.org", "ngo", "NGO B", lat=40.8500, lng=-73.8500, capacity=10)
    
    # NGO C: ~58km away (41.1000, -73.7000) -> outside 30km
    register_and_login_user("ngo-c@foodbridge.org", "ngo", "NGO C", lat=41.1000, lng=-73.7000, capacity=100)

    # 3. Trigger matching
    match_res = client.post(
        f"/api/v1/match/{donation_id}",
        headers={"X-Internal-Token": "super_secret_internal_key_999"}
    )
    assert match_res.status_code == status.HTTP_201_CREATED
    matches = match_res.json()
    assert len(matches) == 2

    # Verify allocation
    # NGO A (nearest) gets 10 units
    # NGO B (next nearest, outside 15km but within 30km) gets remaining 5 units
    match_a = next(m for m in matches if m["ngo_id"] == 1)
    match_b = next(m for m in matches if m["ngo_id"] == 2)
    
    assert match_a["quantity_allocated"] == 10
    assert match_b["quantity_allocated"] == 5
    assert match_a["status"] == "pending"
    assert match_b["status"] == "pending"

    # Verify donation status is now "matched"
    don_get = client.get(f"/api/v1/donations/{donation_id}")
    assert don_get.json()["status"] == "matched"

def test_ngo_accept_match():
    """Verifies that an NGO can accept a pending match, reducing capacity."""
    # Setup database with a donation and matching NGO
    rest_token = register_and_login_user("rest@test.org", "restaurant", "Test Bistro", lat=40.7128, lng=-74.0060)
    donation_id = client.post(
        "/api/v1/donations",
        json={
            "food_type": "Bread",
            "quantity": "5 units",
            "prep_time": datetime.datetime.utcnow().isoformat(),
            "expiry_minutes": 60,
            "pickup_address": "Test Bistro",
            "pickup_lat": 40.7128,
            "pickup_lng": -74.0060
        },
        headers={"Authorization": f"Bearer {rest_token}"}
    ).json()["id"]

    ngo_token = register_and_login_user("ngo-accept@test.org", "ngo", "NGO Accept", lat=40.7150, lng=-74.0080, capacity=20)
    
    # Run matching
    match_res = client.post(
        f"/api/v1/match/{donation_id}",
        headers={"X-Internal-Token": "super_secret_internal_key_999"}
    )
    match_id = match_res.json()[0]["id"]

    # 1. Reject accepting with another user or volunteer (RBAC)
    vol_token = register_and_login_user("vol@test.org", "volunteer", "Vol John")
    res = client.patch(f"/api/v1/match/{match_id}/accept", headers={"Authorization": f"Bearer {vol_token}"})
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 2. Accept with the matched NGO
    res = client.patch(
        f"/api/v1/match/{match_id}/accept",
        headers={"Authorization": f"Bearer {ngo_token}"}
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "accepted"

    # 3. Verify NGO capacity has decreased from 20 to 15
    db = TestingSessionLocal()
    ngo = db.query(NGOProfile).filter(NGOProfile.id == 1).first()
    assert ngo.capacity == 15
    db.close()

def test_ngo_reject_match_and_rematch():
    """
    Verifies that when an NGO rejects a match:
    - Match is marked rejected
    - Other pending matches are deleted
    - Donation status resets to "available"
    - Re-matching is automatically triggered (excluding the rejecting NGO)
    """
    # Setup:
    # NGO A: ~5km away, capacity = 10
    # NGO B: ~8km away, capacity = 20
    # Donation: 15 units
    # Initial matching: NGO A matched 10 (pending), NGO B matched 5 (pending)
    rest_token = register_and_login_user("rest-reject@test.org", "restaurant", "Rest Reject", lat=40.7128, lng=-74.0060)
    donation_id = client.post(
        "/api/v1/donations",
        json={
            "food_type": "Cookies",
            "quantity": "15 boxes",
            "prep_time": datetime.datetime.utcnow().isoformat(),
            "expiry_minutes": 100,
            "pickup_address": "Rest Reject",
            "pickup_lat": 40.7128,
            "pickup_lng": -74.0060
        },
        headers={"Authorization": f"Bearer {rest_token}"}
    ).json()["id"]

    ngo_a_token = register_and_login_user("ngo-a-rej@test.org", "ngo", "NGO A", lat=40.7150, lng=-74.0080, capacity=10)
    ngo_b_token = register_and_login_user("ngo-b-rej@test.org", "ngo", "NGO B", lat=40.7500, lng=-73.9400, capacity=20)

    # Initial matching run
    client.post(
        f"/api/v1/match/{donation_id}",
        headers={"X-Internal-Token": "super_secret_internal_key_999"}
    )

    # Fetch initial matches
    matches = client.get(f"/api/v1/match/donation/{donation_id}").json()
    assert len(matches) == 2
    match_a = next(m for m in matches if m["ngo_id"] == 1)
    match_b = next(m for m in matches if m["ngo_id"] == 2)
    assert match_a["quantity_allocated"] == 10
    assert match_b["quantity_allocated"] == 5

    # NGO A rejects their match
    rej_res = client.patch(
        f"/api/v1/match/{match_a['id']}/reject",
        headers={"Authorization": f"Bearer {ngo_a_token}"}
    )
    assert rej_res.status_code == status.HTTP_200_OK
    assert rej_res.json()["status"] == "rejected"

    # Check post-rejection matches state in the DB
    # The rejected match should remain in the database (status = rejected)
    # The other pending match (NGO B's match) should have been deleted prior to re-matching
    # Then the re-matching should have matched the entire 15 units to NGO B (since NGO A is excluded)
    db = TestingSessionLocal()
    all_matches = db.query(Match).filter(Match.donation_id == donation_id).all()
    
    # We should have exactly 2 matches now:
    # 1. NGO A (rejected, quantity=10)
    # 2. NGO B (pending, quantity=15 - from the new run)
    assert len(all_matches) == 2
    
    m_a = next(m for m in all_matches if m.ngo_id == 1)
    m_b = next(m for m in all_matches if m.ngo_id == 2)

    assert m_a.status == "rejected"
    assert m_a.quantity_allocated == 10
    
    assert m_b.status == "pending"
    assert m_b.quantity_allocated == 15

    # The donation status should be back to "matched" after the re-run
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    assert donation.status == "matched"
    
    db.close()
