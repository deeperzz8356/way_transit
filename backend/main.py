from pathlib import Path
import os
import logging
import sys
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("way_transit")

# Load repo-root .env before anything else (OCR / Groq)
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# The backend modules use imports such as ``from database import ...``.
# Uvicorn does not put this directory on sys.path when it is started from the
# repository root with ``uvicorn backend.main:app --reload``.  Make that
# supported launch command resolve the local modules exactly as it does when
# starting from inside ``backend/``.
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from database import engine, Base, SessionLocal
from schema_migrate import ensure_ticket_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize FAISS Vector Store on startup (optional; ticket APIs work without it)
    db = SessionLocal()
    try:
        from rag import sync_db_to_vectorstore
        sync_db_to_vectorstore(db)
    except Exception as exc:
        print(f"[warn] RAG vectorstore sync skipped: {exc}")
    finally:
        db.close()
    yield
    # Shutdown logic if any


import models

Base.metadata.create_all(bind=engine)
ensure_ticket_schema()

app = FastAPI(title="WAY Transit API", version="1.0.0", lifespan=lifespan)

# CORS — allow all origins (Flutter web dev, Vite, mobile, any localhost port).
#
# IMPORTANT: allow_credentials MUST be False when allow_origins=["*"].
# If credentials=True is combined with wildcard origins, Starlette/browsers
# silently drop the Access-Control-Allow-Origin header, causing CORS failures.
# Authentication is handled via Bearer tokens in the Authorization header,
# not cookies, so credentials=False is correct here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

uploads_root = Path(__file__).resolve().parent / "uploads"
uploads_root.mkdir(parents=True, exist_ok=True)
(uploads_root / "tickets").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_root)), name="uploads")

from routes import auth, user, search, booking, agent, user_trips, rides

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(search.router)
app.include_router(booking.router)
app.include_router(agent.router)
app.include_router(user_trips.router)
app.include_router(rides.router)


@app.get("/")
def root():
    return {"message": "WAY Transit API running", "version": "1.0.0"}
