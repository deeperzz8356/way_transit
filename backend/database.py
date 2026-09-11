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
        # Never silently show data from a different SQLite database when a
        # PostgreSQL database was explicitly configured.  A failed connection
        # must stop startup so the issue is visible and the API cannot serve
        # incomplete fallback data.
        raise RuntimeError(
            "PostgreSQL connection failed. The API was not started, so it "
            "cannot fall back to SQLite and serve the wrong database. "
            "Check DATABASE_URL, the database host/port, and network access."
        ) from exc

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()
