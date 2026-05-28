"""
Script to seed the database with sample routes.
Run this after creating tables: python backend/seed_db.py
"""
from database import SessionLocal, engine
from models import Base
import crud
import models

def init_db():
    """Create tables and seed with sample data"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if routes already exist
    existing_routes = db.query(models.Route).count()
    if existing_routes > 0:
        print("✓ Routes already seeded")
        db.close()
        return
    
    # Sample routes
    routes = [
        {
            "source": "Mumbai",
            "destination": "Pune",
            "transport": "bus",
            "departure_time": "06:00 AM",
            "arrival_time": "10:00 AM",
            "price": 300
        },
        {
            "source": "Mumbai",
            "destination": "Pune",
            "transport": "cab",
            "departure_time": "07:00 AM",
            "arrival_time": "10:30 AM",
            "price": 800
        },
        {
            "source": "Mumbai",
            "destination": "Bangalore",
            "transport": "flight",
            "departure_time": "09:00 AM",
            "arrival_time": "12:30 PM",
            "price": 3000
        },
        {
            "source": "Pune",
            "destination": "Delhi",
            "transport": "train",
            "departure_time": "10:00 PM",
            "arrival_time": "06:00 AM",
            "price": 1200
        },
        {
            "source": "Delhi",
            "destination": "Bangalore",
            "transport": "flight",
            "departure_time": "02:00 PM",
            "arrival_time": "05:30 PM",
            "price": 2500
        }
    ]
    
    for route in routes:
        crud.create_route(db, **route)
    
    db.close()
    print(f"✓ Seeded {len(routes)} routes")

if __name__ == "__main__":
    init_db()
