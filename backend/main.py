from pathlib import Path
import os

from dotenv import load_dotenv

# Load repo-root .env before anything else (OCR / Groq)
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

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


Base.metadata.create_all(bind=engine)
ensure_ticket_schema()

app = FastAPI(title="WAY Transit API", version="1.0.0", lifespan=lifespan)

# CORS: allow Flutter web (random localhost ports) + Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_root = Path(__file__).resolve().parent / "uploads"
uploads_root.mkdir(parents=True, exist_ok=True)
(uploads_root / "tickets").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_root)), name="uploads")

from routes import user, search, booking, agent

app.include_router(user.router)
app.include_router(search.router)
app.include_router(booking.router)
app.include_router(agent.router)


@app.get("/")
def root():
    return {"message": "WAY Transit API running", "version": "1.0.0"}
