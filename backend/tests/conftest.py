import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Ensure backend module is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

from backend.app.main import app
from backend.app.core.database import get_db, Base
from backend.app.auth.security import create_access_token
from backend.app.models import User, RestaurantProfile, NGOProfile, VolunteerProfile

# Using pytest-postgresql is requested. Usually you define a postgresql_proc fixture,
# but for simplicity we assume the standard TEST_DB environment URL pattern here 
# if pytest-postgresql overrides it, or we create a fresh one.
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://foodbridge_admin:foodbridge_secure_pass_99@localhost:5432/foodbridge_test_db")

engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def test_db():
    # Setup
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal
    
    # Teardown
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_db):
    session = test_db()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def test_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    def _auth_headers(role: str, email: str = None):
        if not email:
            email = f"test_{role}@foodbridge.ai"
        token = create_access_token(data={"sub": email, "role": role})
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers

@pytest.fixture
def sample_restaurant(db_session):
    user = User(email="restaurant@foodbridge.ai", hashed_password="hashed", role="restaurant")
    db_session.add(user)
    db_session.commit()
    profile = RestaurantProfile(user_id=user.id, name="Test Restaurant", address="123 Test St", latitude=10.0, longitude=20.0)
    db_session.add(profile)
    db_session.commit()
    return profile

@pytest.fixture
def sample_ngo(db_session):
    user = User(email="ngo@foodbridge.ai", hashed_password="hashed", role="ngo")
    db_session.add(user)
    db_session.commit()
    profile = NGOProfile(user_id=user.id, name="Test NGO", registration_number="REG123", address="456 NGO St", capacity=100)
    db_session.add(profile)
    db_session.commit()
    return profile

@pytest.fixture
def sample_volunteer(db_session):
    user = User(email="volunteer@foodbridge.ai", hashed_password="hashed", role="volunteer")
    db_session.add(user)
    db_session.commit()
    profile = VolunteerProfile(user_id=user.id, name="Test Volunteer", phone_number="1234567890", vehicle_type="car")
    db_session.add(profile)
    db_session.commit()
    return profile
