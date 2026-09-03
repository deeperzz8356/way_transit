"""
Phase 2 — create the 3 new ride-booking tables in PostgreSQL and
seed the initial 'mock' provider row.

Run from the backend/ directory:
    venv\\Scripts\\python.exe create_ride_tables.py
"""
import sys
import os

# Ensure backend/ is on the path so our modules resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base, SessionLocal
import models  # registers ALL ORM classes including the new ride ones

print("Database:", engine.url)
print("Creating tables …")
Base.metadata.create_all(bind=engine)

from sqlalchemy import inspect
inspector = inspect(engine)
db_tables = inspector.get_table_names()

targets = ["ride_providers", "cab_rides", "ride_status_history"]
print()
print("=== Ride-booking table status ===")
for t in targets:
    tag = "OK" if t in db_tables else "MISSING"
    print(f"  {t:<35} {tag}")

# ── Show columns for cab_rides ───────────────────────────────────
if "cab_rides" in db_tables:
    print()
    print("=== cab_rides columns ===")
    for col in inspector.get_columns("cab_rides"):
        print(f"  {col['name']:<35} {col['type']}")

# ── Show indexes for cab_rides ───────────────────────────────────
if "cab_rides" in db_tables:
    print()
    print("=== cab_rides indexes ===")
    for idx in inspector.get_indexes("cab_rides"):
        print(f"  {idx['name']:<40} columns={idx['column_names']}")

# ── Seed: mock provider ──────────────────────────────────────────
print()
db = SessionLocal()
try:
    existing = db.query(models.RideProvider).filter_by(name="mock").first()
    if existing:
        print(f"Mock provider already seeded  (id={existing.id})")
    else:
        mock_prov = models.RideProvider(
            name="mock",
            display_name="Mock Provider (Demo)",
            is_active=True,
            is_sandbox=True,
            config='{"note": "Simulated provider for development and testing"}',
        )
        db.add(mock_prov)
        db.commit()
        db.refresh(mock_prov)
        print(f"Seeded mock provider          (id={mock_prov.id})")
finally:
    db.close()

print()
print("Phase 2 complete — all tables ready.")
