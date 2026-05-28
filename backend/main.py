from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routes import user, search, booking

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WAY Transit API", version="1.0.0")

# CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(search.router)
app.include_router(booking.router)

@app.get("/")
def root():
    return {"message": "WAY Transit API running", "version": "1.0.0"}