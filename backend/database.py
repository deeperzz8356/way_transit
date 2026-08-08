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

def _create_engine(url: str):
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine_kwargs = {"connect_args": connect_args} if connect_args else {}
    if url.startswith("postgresql"):
        engine_kwargs["pool_pre_ping"] = True
    return create_engine(url, **engine_kwargs)

engine = _create_engine(DATABASE_URL)

if DATABASE_URL.startswith("postgresql"):
    try:
        with engine.connect():
            pass
    except Exception as exc:
        warnings.warn(
            f"PostgreSQL connection failed for DATABASE_URL={DATABASE_URL}. "
            f"Falling back to SQLite for local startup. Error: {exc}"
        )
        DATABASE_URL = "sqlite:///./way_transit.db"
        engine = _create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()