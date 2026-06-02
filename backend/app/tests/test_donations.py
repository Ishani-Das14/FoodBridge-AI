# ==============================================================================
# FoodBridge AI - Donation Service Test Suite
# Tests donation creation, listing, status transitions, soft deletes, and Celery tasks
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
from app.services.donation.router import router as donation_router
from app.tasks.donation_tasks import expire_donations
import app.tasks.donation_tasks as donation_tasks

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

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Initializes schema before every test and drops it afterward."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# Helper function to register and acquire access tokens for different roles
def register_and_login_user(email: str, role: str, name: str) -> str:
    # 1. Register base account
    if role == "restaurant":
        client.post(
            "/api/v1/auth/register/restaurant",
            json={
                "email": email,
                "password": "securepassword123",
                "name": name,
                "address": "123 Gourmet Ave, Cityville",
                "latitude": 40.7128,
                "longitude": -74.0060
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
                "latitude": 40.7306,
                "longitude": -73.9352
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

def test_create_donation_restaurant_success():
    """Verifies that a restaurant can successfully post a donation."""
    token = register_and_login_user("rest-owner@foodbridge.org", "restaurant", "Bella Bistro")
    headers = {"Authorization": f"Bearer {token}"}
    
    prep_time = datetime.datetime.utcnow().isoformat()
    response = client.post(
        "/api/v1/donations",
        json={
            "food_type": "Fresh Salads",
            "quantity": "10 kg",
            "prep_time": prep_time,
            "expiry_minutes": 120,
            "pickup_address": "123 Gourmet Ave, Cityville",
            "pickup_lat": 40.7128,
            "pickup_lng": -74.0060
        },
        headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["food_type"] == "Fresh Salads"
    assert data["quantity"] == "10 kg"
    assert data["status"] == "available"
    assert data["restaurant_name"] == "Bella Bistro"
    assert "expiry_time" in data

def test_create_donation_invalid_role():
    """Verifies that an NGO or volunteer cannot create a donation."""
    ngo_token = register_and_login_user("ngo-test@foodbridge.org", "ngo", "Charity A")
    headers = {"Authorization": f"Bearer {ngo_token}"}
    
    response = client.post(
        "/api/v1/donations",
        json={
            "food_type": "Fresh Bread",
            "quantity": "5 bags",
            "prep_time": datetime.datetime.utcnow().isoformat(),
            "expiry_minutes": 60,
            "pickup_address": "123 Main St",
            "pickup_lat": 0.0,
            "pickup_lng": 0.0
        },
        headers=headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Only Restaurant accounts can create donation posts" in response.json()["detail"]

def test_list_donations_and_filter_by_city():
    """Verifies querying open donations and filtering by city works correctly."""
    rest1_token = register_and_login_user("nyc-rest@foodbridge.org", "restaurant", "NYC Pizza")
    rest2_token = register_and_login_user("la-rest@foodbridge.org", "restaurant", "LA Burgers")
    
    # 1. Create donation in NYC
    client.post(
        "/api/v1/donations",
        json={
            "food_type": "Pizzas",
            "quantity": "12 boxes",
            "prep_time": datetime.datetime.utcnow().isoformat(),
            "expiry_minutes": 180,
            "pickup_address": "789 Broadway, New York City",
            "pickup_lat": 40.7588,
            "pickup_lng": -73.9851
        },
        headers={"Authorization": f"Bearer {rest1_token}"}
    )

    # 2. Create donation in LA
    client.post(
        "/api/v1/donations",
        json={
            "food_type": "Tacos",
            "quantity": "50 pieces",
            "prep_time": datetime.datetime.utcnow().isoformat(),
            "expiry_minutes": 90,
            "pickup_address": "100 Sunset Blvd, Los Angeles",
            "pickup_lat": 34.0522,
            "pickup_lng": -118.2437
        },
        headers={"Authorization": f"Bearer {rest2_token}"}
    )

    # 3. List all
    res_all = client.get("/api/v1/donations")
    assert res_all.status_code == status.HTTP_200_OK
    assert len(res_all.json()) == 2

    # 4. Filter by New York
    res_nyc = client.get("/api/v1/donations?city=New York")
    assert len(res_nyc.json()) == 1
    assert res_nyc.json()[0]["food_type"] == "Pizzas"

    # 5. Filter by Los Angeles
    res_la = client.get("/api/v1/donations?city=Los Angeles")
    assert len(res_la.json()) == 1
    assert res_la.json()[0]["food_type"] == "Tacos"

def test_get_single_donation():
    """Verifies getting a single donation by ID."""
    token = register_and_login_user("bella@foodbridge.org", "restaurant", "Bella Bistro")
    
    create_res = client.post(
        "/api/v1/donations",
        json={
            "food_type": "Pasta",
            "quantity": "3 trays",
            "prep_time": datetime.datetime.utcnow().isoformat(),
            "expiry_minutes": 120,
            "pickup_address": "123 Gourmet Ave, Cityville",
            "pickup_lat": 40.7128,
            "pickup_lng": -74.0060
        },
        headers={"Authorization": f"Bearer {token}"}
    ).json()

    res = client.get(f"/api/v1/donations/{create_res['id']}")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["food_type"] == "Pasta"
    assert res.json()["restaurant_name"] == "Bella Bistro"

def test_get_nonexistent_donation_returns_404():
    """Verifies querying a missing donation ID yields a 404."""
    res = client.get("/api/v1/donations/999")
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_status_transitions_rbac():
    """Verifies that role clearances control allowed status transitions."""
    rest_token = register_and_login_user("rest-rbac-don@foodbridge.org", "restaurant", "RBAC Grill")
    vol_token = register_and_login_user("vol-rbac-don@foodbridge.org", "volunteer", "Vol John")
    ngo_token = register_and_login_user("ngo-rbac-don@foodbridge.org", "ngo", "NGO Hope")

    # 1. Create donation
    donation = client.post(
        "/api/v1/donations",
        json={
            "food_type": "Burgers",
            "quantity": "15 pieces",
            "prep_time": datetime.datetime.utcnow().isoformat(),
            "expiry_minutes": 120,
            "pickup_address": "123 Gourmet Ave, Cityville",
            "pickup_lat": 40.7128,
            "pickup_lng": -74.0060
        },
        headers={"Authorization": f"Bearer {rest_token}"}
    ).json()

    # 2. Volunteer sets 'picked_up' -> OK (HTTP 200)
    res = client.patch(
        f"/api/v1/donations/{donation['id']}/status",
        json={"status": "picked_up"},
        headers={"Authorization": f"Bearer {vol_token}"}
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "picked_up"

    # 3. Volunteer tries to set 'delivered' -> Forbidden (HTTP 403)
    res = client.patch(
        f"/api/v1/donations/{donation['id']}/status",
        json={"status": "delivered"},
        headers={"Authorization": f"Bearer {vol_token}"}
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 4. NGO sets 'delivered' -> OK (HTTP 200)
    res = client.patch(
        f"/api/v1/donations/{donation['id']}/status",
        json={"status": "delivered"},
        headers={"Authorization": f"Bearer {ngo_token}"}
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "delivered"

def test_delete_donation_ownership():
    """Verifies that only the posting restaurant owner can delete (soft-delete) the donation."""
    owner_token = register_and_login_user("owner@foodbridge.org", "restaurant", "My Kitchen")
    other_token = register_and_login_user("other@foodbridge.org", "restaurant", "Other Kitchen")
    
    # 1. Create donation
    donation = client.post(
        "/api/v1/donations",
        json={
            "food_type": "Soup",
            "quantity": "2 pots",
            "prep_time": datetime.datetime.utcnow().isoformat(),
            "expiry_minutes": 60,
            "pickup_address": "123 Gourmet Ave, Cityville",
            "pickup_lat": 40.7128,
            "pickup_lng": -74.0060
        },
        headers={"Authorization": f"Bearer {owner_token}"}
    ).json()

    # 2. Other restaurant tries to delete -> Forbidden (HTTP 403)
    res = client.delete(
        f"/api/v1/donations/{donation['id']}",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 3. Owner deletes -> OK (HTTP 200, status marked as 'expired')
    res = client.delete(
        f"/api/v1/donations/{donation['id']}",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "expired"

def test_expire_donations_celery_task():
    """Verifies the expire_donations background task sweeps past-expiry available posts."""
    rest_token = register_and_login_user("sweeper@foodbridge.org", "restaurant", "Sweep Diner")
    
    # 1. Create a donation that is already expired (prep_time is 4 hours ago, expires in 30 mins)
    past_prep_time = (datetime.datetime.utcnow() - datetime.timedelta(hours=4)).isoformat()
    client.post(
        "/api/v1/donations",
        json={
            "food_type": "Expired Milk",
            "quantity": "10 cartons",
            "prep_time": past_prep_time,
            "expiry_minutes": 30,
            "pickup_address": "123 Sweep Rd, Cityville",
            "pickup_lat": 40.0,
            "pickup_lng": -70.0
        },
        headers={"Authorization": f"Bearer {rest_token}"}
    )

    # 2. Create an active donation that is NOT expired (prep_time is now, expires in 60 mins)
    client.post(
        "/api/v1/donations",
        json={
            "food_type": "Fresh Bread",
            "quantity": "5 loaves",
            "prep_time": datetime.datetime.utcnow().isoformat(),
            "expiry_minutes": 60,
            "pickup_address": "123 Sweep Rd, Cityville",
            "pickup_lat": 40.0,
            "pickup_lng": -70.0
        },
        headers={"Authorization": f"Bearer {rest_token}"}
    )

    # 3. Assert both are active 'available' right now
    res_list = client.get("/api/v1/donations")
    assert len(res_list.json()) == 2

    # 4. Trigger the Celery expire sweep task synchronously
    task_result = expire_donations()
    assert "Expired 1 donations" in task_result

    # 5. Assert only 1 active donation remains in the query list
    res_list_after = client.get("/api/v1/donations")
    assert len(res_list_after.json()) == 1
    assert res_list_after.json()[0]["food_type"] == "Fresh Bread"
