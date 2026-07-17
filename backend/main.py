from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base, SessionLocal
from rag import sync_db_to_vectorstore

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize FAISS Vector Store on startup
    db = SessionLocal()
    try:
        sync_db_to_vectorstore(db)
    finally:
        db.close()
    yield
    # Shutdown logic if any

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WAY Transit API", version="1.0.0", lifespan=lifespan)

# CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes import user, search, booking, agent

app.include_router(user.router)
app.include_router(search.router)
app.include_router(booking.router)
app.include_router(agent.router)


@app.get("/")
def root():
    return {"message": "WAY Transit API running", "version": "1.0.0"}