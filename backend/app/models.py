# ==============================================================================
# FoodBridge AI - Database Models
# Defines schema blueprints for core user profiles and role-specific models
# ==============================================================================
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False) # restaurant, ngo, volunteer, government
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships to profiles
    restaurant_profile = relationship("RestaurantProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    ngo_profile = relationship("NGOProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    volunteer_profile = relationship("VolunteerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class RestaurantProfile(Base):
    __tablename__ = "restaurant_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    user = relationship("User", back_populates="restaurant_profile")
    donations = relationship("Donation", back_populates="restaurant", cascade="all, delete-orphan")

class NGOProfile(Base):
    __tablename__ = "ngo_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    registration_number = Column(String, unique=True, nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    capacity = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="ngo_profile")

class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=True) # car, bicycle, walking, motorcycle, etc.

    user = relationship("User", back_populates="volunteer_profile")

class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurant_profiles.id", ondelete="CASCADE"), nullable=False)
    food_type = Column(String, nullable=False)
    quantity = Column(String, nullable=False)
    prep_time = Column(DateTime, nullable=False)
    expiry_time = Column(DateTime, nullable=False)
    pickup_address = Column(String, nullable=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lng = Column(Float, nullable=False)
    status = Column(String, default="available", nullable=False) # available, picked_up, delivered, expired
    packaging_type = Column(String, nullable=True) # sealed, open, semi_sealed
    storage_temp = Column(String, nullable=True) # hot, cold, ambient
    allergen_tags = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    restaurant = relationship("RestaurantProfile", back_populates="donations")
    matches = relationship("Match", back_populates="donation", cascade="all, delete-orphan")

    @property
    def restaurant_name(self) -> str:
        return self.restaurant.name if self.restaurant else ""

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(Integer, ForeignKey("donations.id", ondelete="CASCADE"), nullable=False)
    ngo_id = Column(Integer, ForeignKey("ngo_profiles.id", ondelete="CASCADE"), nullable=False)
    quantity_allocated = Column(Integer, nullable=False)
    status = Column(String, default="pending", nullable=False) # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    donation = relationship("Donation", back_populates="matches")
    ngo = relationship("NGOProfile")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User")
