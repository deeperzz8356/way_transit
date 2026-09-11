"""Travel History and Statistics API.

Endpoints:
  GET    /trips                 – list current user's trips (with filters)
  POST   /trips                 – create a manual trip (walking, etc.)
  GET    /trips/{id}            – trip detail
  PUT    /trips/{id}            – update trip
  DELETE /trips/{id}            – delete trip
  GET    /stats/overview        – travel statistics for current user
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import crud
import schemas
from database import SessionLocal
from dependencies import get_current_user

logger = logging.getLogger("way_transit")

router = APIRouter(tags=["trips"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Trips ───────────────────────────────────

@router.get("/trips", response_model=list[schemas.UserTripResponse])
def list_trips(
    status: Optional[str] = Query(None, description="all|planned|started|completed|cancelled"),
    transport_mode: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's travel history, newest first."""
    trips = crud.get_user_trips(
        db,
        user_id=user_id,
        status=status,
        transport_mode=transport_mode,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return trips


@router.post("/trips", response_model=schemas.UserTripResponse, status_code=201)
def create_trip(
    data: schemas.UserTripCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually create a trip (e.g. walking, manual entry)."""
    trip = crud.create_user_trip(db, user_id=user_id, data=data)
    logger.info("Created manual trip id=%s for user_id=%s", trip.id, user_id)
    return trip


@router.get("/trips/{trip_id}", response_model=schemas.UserTripResponse)
def get_trip(
    trip_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detail for a single trip. Only the owner can view it."""
    trip = crud.get_user_trip_by_id(db, trip_id=trip_id, user_id=user_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.put("/trips/{trip_id}", response_model=schemas.UserTripResponse)
def update_trip(
    trip_id: int,
    data: schemas.UserTripUpdate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update trip fields. Only the owner can update."""
    trip = crud.get_user_trip_by_id(db, trip_id=trip_id, user_id=user_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    updated = crud.update_user_trip(db, trip=trip, data=data)
    return updated


@router.delete("/trips/{trip_id}", status_code=204)
def delete_trip(
    trip_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a trip. Only the owner can delete it."""
    trip = crud.get_user_trip_by_id(db, trip_id=trip_id, user_id=user_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    crud.delete_user_trip(db, trip)


# ─── Statistics ───────────────────────────────

@router.get("/stats/overview", response_model=schemas.TravelStatsOverview)
def get_stats_overview(
    period: str = Query(
        "all_time",
        description="Filter period: all_time | this_week | this_month | last_3_months | this_year",
    ),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return aggregated travel statistics for the authenticated user."""
    valid_periods = {"all_time", "this_week", "this_month", "last_3_months", "this_year"}
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period. Valid values: {valid_periods}")
    stats = crud.compute_travel_stats(db, user_id=user_id, period=period)
    return stats
