# ==============================================================================
# FoodBridge AI - Database Configuration
# Configures SQLAlchemy engine, sessionmaker, and Base model
# ==============================================================================
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Retrieve database connection parameters from environment
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "foodbridge_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "foodbridge_secure_pass_99")
POSTGRES_DB = os.getenv("POSTGRES_DB", "foodbridge_db")

# Compute database URL or use from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./foodbridge.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# DB Session Dependency Generator
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
