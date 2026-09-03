"""
Script to seed the database with sample GTFS-like routes and ride providers.
Run this after creating tables: python backend/seed_db.py
"""
from database import SessionLocal, engine
from models import Base
import crud
import models

def _seed_ride_providers(db):
    """Seed available ride providers (mock, uber, etc.)."""
    providers_to_seed = [
        {
            "name": "mock",
            "display_name": "Mock Provider (Demo)",
            "is_active": True,
            "is_sandbox": True,
            "config": '{"note": "Simulated provider for development and testing"}',
        },
        {
            "name": "uber",
            "display_name": "Uber",
            "is_active": False,  # Inactive until credentials are provided
            "is_sandbox": False,
            "config": '{"api_version": "v1", "mode": "guest_rides", "note": "Requires UBER_CLIENT_ID and UBER_CLIENT_SECRET"}',
        },
    ]

    for provider_data in providers_to_seed:
        existing = db.query(models.RideProvider).filter_by(name=provider_data["name"]).first()
        if existing:
            # Update if already exists
            for key, value in provider_data.items():
                setattr(existing, key, value)
            db.commit()
            print(f"Updated provider: {provider_data['name']}")
        else:
            # Create new
            provider = models.RideProvider(**provider_data)
            db.add(provider)
            db.commit()
            print(f"Seeded provider: {provider_data['name']}")

def init_db():
    """Create tables and seed with sample data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ── Seed ride providers ────────────────────────────────────────────────
    _seed_ride_providers(db)

    existing_routes = {
        (route.source, route.destination, route.transport, route.departure_time, route.arrival_time, route.price)
        for route in db.query(models.Route).all()
    }

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
            "destination": "Pune",
            "transport": "train",
            "departure_time": "06:45 AM",
            "arrival_time": "09:15 AM",
            "price": 220
        },
        {
            "source": "Mumbai",
            "destination": "Pune",
            "transport": "metro+bus",
            "departure_time": "06:20 AM",
            "arrival_time": "09:50 AM",
            "price": 180
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
            "source": "Mumbai",
            "destination": "Navi Mumbai",
            "transport": "metro",
            "departure_time": "08:00 AM",
            "arrival_time": "08:45 AM",
            "price": 60
        },
        {
            "source": "Navi Mumbai",
            "destination": "Pune",
            "transport": "bus",
            "departure_time": "09:30 AM",
            "arrival_time": "12:45 PM",
            "price": 280
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
            "source": "Pune",
            "destination": "Mumbai",
            "transport": "bus",
            "departure_time": "05:30 PM",
            "arrival_time": "09:30 PM",
            "price": 300
        },
        {
            "source": "Delhi",
            "destination": "Bangalore",
            "transport": "flight",
            "departure_time": "02:00 PM",
            "arrival_time": "05:30 PM",
            "price": 2500
        },
        {
            "source": "Delhi",
            "destination": "Mumbai",
            "transport": "train",
            "departure_time": "09:15 PM",
            "arrival_time": "07:45 AM",
            "price": 1400
        },
        {
            "source": "Bangalore",
            "destination": "Mumbai",
            "transport": "flight",
            "departure_time": "08:30 AM",
            "arrival_time": "10:45 AM",
            "price": 3200
        }
    ]
    
    inserted = 0
    for route in routes:
        signature = (
            route["source"],
            route["destination"],
            route["transport"],
            route["departure_time"],
            route["arrival_time"],
            route["price"],
        )
        if signature in existing_routes:
            continue
        crud.create_route(db, **route)
        inserted += 1
    
    db.close()
    print(f"Seeded {inserted} new routes")

if __name__ == "__main__":
    init_db()
