from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import warnings

try:
    from dotenv import load_dotenv
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(base_dir, ".env"))
except Exception:
    warnings.warn("python-dotenv not installed; continuing without loading .env")

# Use environment variable or default to SQLite for MVP
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./way_transit.db"  # SQLite for local MVP testing
)

# For PostgreSQL, use: DATABASE_URL=postgresql://user:password@localhost:5432/way_transit

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()