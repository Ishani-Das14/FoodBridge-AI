# ==============================================================================
# FoodBridge AI - Authentication Test Suite
# Tests registration, authentication, token refresh, and RBAC authorization
# ==============================================================================
import pytest
from fastapi import FastAPI, Depends, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.auth.dependencies import get_current_user, role_required
from app.auth.router import router as auth_router
import app.auth.service as auth_service

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

# ------------------------------------------------------------------------------
# 2. Redis Mock Setup for Environment-Independent Caching Tests
# ------------------------------------------------------------------------------
class MockRedis:
    def __init__(self):
        self.store = {}

    def setex(self, name: str, time: int, value: str):
        self.store[name] = value
        return True

    def get(self, name: str):
        return self.store.get(name)

    def delete(self, *names):
        count = 0
        for name in names:
            if name in self.store:
                del self.store[name]
                count += 1
        return count

# Monkeypatch the Redis client in the auth service
mock_redis = MockRedis()
auth_service.redis_client = mock_redis

# ------------------------------------------------------------------------------
# 3. Test App Initialization & Router Mounting
# ------------------------------------------------------------------------------
app = FastAPI()
app.dependency_overrides[get_db] = override_get_db
app.include_router(auth_router, prefix="/api/v1")

# Create a test route to verify Role-Based Access Control (RBAC)
@app.get("/api/v1/test-restaurant-only")
def route_restaurant_only(user=Depends(role_required("restaurant"))):
    return {"message": f"Welcome, Restaurant {user.restaurant_profile.name}!"}

@app.get("/api/v1/test-ngo-only")
def route_ngo_only(user=Depends(role_required("ngo"))):
    return {"message": f"Welcome, NGO {user.ngo_profile.name}!"}

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Initializes schema before every test and drops it afterward."""
    Base.metadata.create_all(bind=engine)
    # Clear the mock redis store
    mock_redis.store.clear()
    yield
    Base.metadata.drop_all(bind=engine)

# ------------------------------------------------------------------------------
# 4. Test Scenarios
# ------------------------------------------------------------------------------

def test_register_restaurant_success():
    """Verifies that a restaurant account is registered and profile created."""
    response = client.post(
        "/api/v1/auth/register/restaurant",
        json={
            "email": "restaurant@foodbridge.org",
            "password": "securepassword123",
            "name": "Central Kitchen",
            "address": "123 Gourmet Ave, Cityville",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "restaurant@foodbridge.org"
    assert data["role"] == "restaurant"
    assert data["restaurant_profile"]["name"] == "Central Kitchen"
    assert data["restaurant_profile"]["address"] == "123 Gourmet Ave, Cityville"
    assert data["ngo_profile"] is None

def test_register_ngo_success():
    """Verifies that an NGO account is registered and profile created."""
    response = client.post(
        "/api/v1/auth/register/ngo",
        json={
            "email": "ngo@foodbridge.org",
            "password": "charitypassword123",
            "name": "Food For All",
            "registration_number": "NGO-998811",
            "address": "456 Hope Street, Cityville",
            "latitude": 40.7306,
            "longitude": -73.9352
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "ngo@foodbridge.org"
    assert data["role"] == "ngo"
    assert data["ngo_profile"]["name"] == "Food For All"
    assert data["ngo_profile"]["registration_number"] == "NGO-998811"

def test_register_volunteer_success():
    """Verifies that a volunteer account is registered and profile created."""
    response = client.post(
        "/api/v1/auth/register/volunteer",
        json={
            "email": "volunteer@foodbridge.org",
            "password": "volunteerpassword123",
            "name": "John Doe",
            "phone_number": "+15550199",
            "vehicle_type": "bicycle"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "volunteer@foodbridge.org"
    assert data["role"] == "volunteer"
    assert data["volunteer_profile"]["name"] == "John Doe"
    assert data["volunteer_profile"]["vehicle_type"] == "bicycle"

def test_register_duplicate_email():
    """Verifies registration fails when an email is already bound to an account."""
    # Register first account
    client.post(
        "/api/v1/auth/register/restaurant",
        json={
            "email": "dup@foodbridge.org",
            "password": "password123",
            "name": "Kitchen A",
            "address": "123 St"
        }
    )
    
    # Try registering second account with the same email
    response = client.post(
        "/api/v1/auth/register/restaurant",
        json={
            "email": "dup@foodbridge.org",
            "password": "password456",
            "name": "Kitchen B",
            "address": "456 Rd"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email address already exists" in response.json()["detail"]

def test_login_success():
    """Verifies login generates access + refresh tokens and caches refresh token."""
    # 1. Register a user
    client.post(
        "/api/v1/auth/register/restaurant",
        json={
            "email": "login@foodbridge.org",
            "password": "securepassword123",
            "name": "Central Kitchen",
            "address": "123 Gourmet Ave, Cityville"
        }
    )

    # 2. Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@foodbridge.org",
            "password": "securepassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # 3. Verify it was cached in mock Redis
    cached = mock_redis.get("foodbridge:refresh_token:1")
    assert cached == data["refresh_token"]

def test_login_invalid_credentials():
    """Verifies login fails with incorrect password."""
    client.post(
        "/api/v1/auth/register/restaurant",
        json={
            "email": "wrongpass@foodbridge.org",
            "password": "correctpassword",
            "name": "Central Kitchen",
            "address": "123 Gourmet Ave, Cityville"
        }
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpass@foodbridge.org",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in response.json()["detail"]

def test_refresh_token_success():
    """Verifies that a valid refresh token yields new access and refresh tokens."""
    # 1. Register and Login
    client.post(
        "/api/v1/auth/register/restaurant",
        json={
            "email": "refresh@foodbridge.org",
            "password": "securepassword123",
            "name": "Central Kitchen",
            "address": "123 Gourmet Ave, Cityville"
        }
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "refresh@foodbridge.org",
            "password": "securepassword123"
        }
    ).json()

    # Sleep slightly to ensure the Unix timestamp of exp changes (JWT exp is in whole seconds)
    import time
    time.sleep(1.1)

    # 2. Refresh Token Exchange
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_res["refresh_token"]}
    )
    assert refresh_res.status_code == status.HTTP_200_OK
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"] != login_res["refresh_token"]

    # 3. Ensure the old refresh token is overwritten with the new one in Redis
    cached = mock_redis.get("foodbridge:refresh_token:1")
    assert cached == new_tokens["refresh_token"]

def test_refresh_token_hijacked_revocation():
    """Verifies token hijacking defense: invalidates session if token doesn't match cache."""
    client.post(
        "/api/v1/auth/register/restaurant",
        json={
            "email": "hijack@foodbridge.org",
            "password": "securepassword123",
            "name": "Central Kitchen",
            "address": "123 Gourmet Ave, Cityville"
        }
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "hijack@foodbridge.org",
            "password": "securepassword123"
        }
    ).json()

    # Artificially alter the token in Redis to simulate a stale/stolen session
    mock_redis.setex("foodbridge:refresh_token:1", 600, "some_other_stale_token")

    # Attempt refresh with the user's token (should fail and trigger absolute revocation)
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_res["refresh_token"]}
    )
    assert refresh_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "revoked, stale, or hijacked" in refresh_res.json()["detail"]
    
    # Assert complete revocation (Redis key deleted)
    assert mock_redis.get("foodbridge:refresh_token:1") is None

def test_get_current_user_profile():
    """Verifies /me endpoint returns the correct user profile details."""
    client.post(
        "/api/v1/auth/register/restaurant",
        json={
            "email": "me@foodbridge.org",
            "password": "securepassword123",
            "name": "Central Kitchen",
            "address": "123 Gourmet Ave, Cityville"
        }
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "me@foodbridge.org",
            "password": "securepassword123"
        }
    ).json()

    headers = {"Authorization": f"Bearer {login_res['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == status.HTTP_200_OK
    data = me_res.json()
    assert data["email"] == "me@foodbridge.org"
    assert data["role"] == "restaurant"
    assert data["restaurant_profile"]["name"] == "Central Kitchen"

def test_rbac_clearance():
    """Verifies that role authorization permits valid access and forbids wrong roles."""
    # 1. Register a Restaurant and an NGO
    client.post(
        "/api/v1/auth/register/restaurant",
        json={
            "email": "rest-rbac@foodbridge.org",
            "password": "securepassword123",
            "name": "RBAC Bistro",
            "address": "123 Gourmet Ave, Cityville"
        }
    )
    client.post(
        "/api/v1/auth/register/ngo",
        json={
            "email": "ngo-rbac@foodbridge.org",
            "password": "securepassword123",
            "name": "RBAC Charity",
            "registration_number": "NGO-12345",
            "address": "456 Hope Street, Cityville"
        }
    )

    # 2. Login both to acquire tokens
    rest_token = client.post(
        "/api/v1/auth/login",
        json={"email": "rest-rbac@foodbridge.org", "password": "securepassword123"}
    ).json()["access_token"]
    
    ngo_token = client.post(
        "/api/v1/auth/login",
        json={"email": "ngo-rbac@foodbridge.org", "password": "securepassword123"}
    ).json()["access_token"]

    # 3. Test Access to Restaurant Only Endpoint
    # - Restaurant accessing restaurant endpoint: OK (HTTP 200)
    res = client.get(
        "/api/v1/test-restaurant-only",
        headers={"Authorization": f"Bearer {rest_token}"}
    )
    assert res.status_code == status.HTTP_200_OK
    assert "Welcome, Restaurant RBAC Bistro!" in res.json()["message"]

    # - NGO accessing restaurant endpoint: Forbidden (HTTP 403)
    res = client.get(
        "/api/v1/test-restaurant-only",
        headers={"Authorization": f"Bearer {ngo_token}"}
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "requires a 'restaurant' account clearance" in res.json()["detail"]

    # 4. Test Access to NGO Only Endpoint
    # - NGO accessing NGO endpoint: OK (HTTP 200)
    res = client.get(
        "/api/v1/test-ngo-only",
        headers={"Authorization": f"Bearer {ngo_token}"}
    )
    assert res.status_code == status.HTTP_200_OK
    assert "Welcome, NGO RBAC Charity!" in res.json()["message"]

    # - Restaurant accessing NGO endpoint: Forbidden (HTTP 403)
    res = client.get(
        "/api/v1/test-ngo-only",
        headers={"Authorization": f"Bearer {rest_token}"}
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "requires a 'ngo' account clearance" in res.json()["detail"]

def test_invalid_token_returns_401():
    """Verifies that requests with malformed or invalid tokens yield HTTP 401 Unauthorized."""
    res = client.get(
        "/api/v1/test-restaurant-only",
        headers={"Authorization": "Bearer malformed_token_string"}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Session has expired or is invalid" in res.json()["detail"]
