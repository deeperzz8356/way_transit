"""
backend/routes/rides.py

Cab / on-demand ride-booking endpoints.

Endpoints:
  POST  /rides/products          – list available ride types & fares
  POST  /rides/book              – book a ride
  GET   /rides/history           – user's ride history
  GET   /rides/{ride_id}         – single ride detail
  POST  /rides/{ride_id}/cancel  – cancel a ride
  POST  /rides/{ride_id}/status  – (internal/debug) force a status transition
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import crud
import schemas
from database import SessionLocal
from dependencies import get_current_user
from services.providers.base_provider import get_provider
from services.routing_service import get_route

logger = logging.getLogger("way_transit")

router = APIRouter(prefix="/rides", tags=["rides"])

# ─── DB dependency ─────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Helpers ───────────────────────────────────────────────────────────────────

_VALID_STATUSES = {
    "REQUESTED", "CONFIRMED", "ARRIVING",
    "IN_PROGRESS", "COMPLETED", "CANCELLED", "FAILED",
}

_CANCELLABLE_STATUSES = {"REQUESTED", "CONFIRMED", "ARRIVING"}


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/products",
    response_model=schemas.RideProductsResponse,
    summary="List available ride types and fare estimates",
)
def get_ride_products(
    data: schemas.RideProductsRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Given pickup and destination coordinates, return all available ride
    products for the selected provider with fare ranges and ETA estimates.

    This is the first call in the booking flow: the Flutter client uses it
    to populate the 'Choose a ride' screen.
    """
    # Validate provider exists in DB
    try:
        crud.get_active_provider(db, name=data.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Compute route (ORS or haversine fallback)
    route = get_route(
        data.pickup_lat,
        data.pickup_lon,
        data.destination_lat,
        data.destination_lon,
    )

    # Get products from the provider
    provider = get_provider(data.provider)
    products = provider.get_products(
        pickup_lat=data.pickup_lat,
        pickup_lon=data.pickup_lon,
        dest_lat=data.destination_lat,
        dest_lon=data.destination_lon,
        distance_km=route.distance_km,
        duration_minutes=route.duration_minutes,
    )

    logger.info(
        "Products requested: user=%d provider=%s dist=%.1fkm eta=%dmin source=%s",
        user_id, data.provider, route.distance_km, route.duration_minutes, route.source,
    )

    return schemas.RideProductsResponse(
        provider=data.provider,
        distance_km=route.distance_km,
        duration_minutes=route.duration_minutes,
        routing_source=route.source,
        products=[
            schemas.RideProductResponse(
                product_id=p.product_id,
                name=p.name,
                description=p.description,
                icon=p.icon,
                capacity=p.capacity,
                currency=p.currency,
                estimated_fare_min=p.estimated_fare_min,
                estimated_fare_max=p.estimated_fare_max,
                estimated_fare=p.estimated_fare,
                estimated_duration_minutes=p.estimated_duration_minutes,
                estimated_distance_km=p.estimated_distance_km,
            )
            for p in products
        ],
    )


@router.post(
    "/book",
    response_model=schemas.CabRideResponse,
    status_code=201,
    summary="Book a ride",
)
def book_ride(
    data: schemas.RideBookRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Request a ride from the selected provider.

    Flow:
      1. Validate provider
      2. Re-compute route (ensures freshest ETA/distance at booking time)
      3. Get fare estimate for the selected product
      4. Call provider.book()
      5. Persist the CabRide row + first status history entry
      6. Return the full ride object
    """
    # 1. Validate provider
    try:
        provider_row = crud.get_active_provider(db, name=data.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # 2. Route
    route = get_route(
        data.pickup_lat,
        data.pickup_lon,
        data.destination_lat,
        data.destination_lon,
    )

    # 3. Fare estimate for the chosen product
    provider = get_provider(data.provider)
    try:
        estimate = provider.estimate(
            product_id=data.product_id,
            pickup_lat=data.pickup_lat,
            pickup_lon=data.pickup_lon,
            dest_lat=data.destination_lat,
            dest_lon=data.destination_lon,
            distance_km=route.distance_km,
            duration_minutes=route.duration_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # 4. Book with provider
    try:
        booking = provider.book(
            product_id=data.product_id,
            pickup_lat=data.pickup_lat,
            pickup_lon=data.pickup_lon,
            pickup_address=data.pickup_address,
            dest_lat=data.destination_lat,
            dest_lon=data.destination_lon,
            dest_address=data.destination_address,
            user_id=user_id,
        )
    except Exception as exc:
        logger.exception("Provider booking failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Provider error: {exc}")

    # 5. Persist
    ride = crud.create_cab_ride(
        db=db,
        user_id=user_id,
        provider_id=provider_row.id,
        provider=data.provider,
        provider_ride_id=booking.provider_ride_id,
        provider_status=booking.provider_status,
        pickup_lat=data.pickup_lat,
        pickup_lon=data.pickup_lon,
        pickup_address=data.pickup_address,
        destination_lat=data.destination_lat,
        destination_lon=data.destination_lon,
        destination_address=data.destination_address,
        ride_type=data.product_id,
        ride_type_name=estimate.name,
        ride_type_icon=estimate.icon,
        estimated_fare_min=estimate.estimated_fare_min,
        estimated_fare_max=estimate.estimated_fare_max,
        estimated_fare=estimate.estimated_fare,
        estimated_distance_km=route.distance_km,
        estimated_duration_minutes=route.duration_minutes,
        payment_method=data.payment_method or "cash",
        status=booking.status,
    )

    logger.info(
        "Ride booked: ride_id=%d user=%d provider=%s product=%s fare=%.0f",
        ride.id, user_id, data.provider, data.product_id, estimate.estimated_fare,
    )
    return ride


@router.get(
    "/history",
    response_model=List[schemas.CabRideResponse],
    summary="User's cab ride history",
)
def get_ride_history(
    status: Optional[str] = Query(None, description="Filter by status (e.g. COMPLETED)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's cab ride history, newest first."""
    if status and status.upper() not in _VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid values: {sorted(_VALID_STATUSES)}",
        )
    return crud.get_user_cab_rides(
        db, user_id=user_id, limit=limit, offset=offset, status=status
    )


@router.get(
    "/{ride_id}",
    response_model=schemas.CabRideResponse,
    summary="Get a single ride",
)
def get_ride(
    ride_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return full detail (including status history) for one ride."""
    ride = crud.get_cab_ride(db, ride_id=ride_id, user_id=user_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride


@router.post(
    "/{ride_id}/cancel",
    response_model=schemas.CabRideResponse,
    summary="Cancel a ride",
)
def cancel_ride(
    ride_id: int,
    data: schemas.RideCancelRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel a ride. Only rides in REQUESTED / CONFIRMED / ARRIVING
    status can be cancelled.
    """
    ride = crud.get_cab_ride(db, ride_id=ride_id, user_id=user_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    if ride.status not in _CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel a ride with status '{ride.status}'.",
        )

    # Notify provider
    try:
        provider = get_provider(ride.provider)
        cancel_result = provider.cancel(
            provider_ride_id=ride.provider_ride_id or "",
            reason=data.reason or "Cancelled by user",
        )
        if not cancel_result.success:
            raise HTTPException(
                status_code=502,
                detail=f"Provider could not cancel: {cancel_result.message}",
            )
    except Exception as exc:
        logger.warning("Provider cancel failed (ride=%d): %s", ride_id, exc)
        # Don't block the user — still mark as cancelled locally
        # This is a design decision: user experience > strict provider sync

    updated_ride = crud.update_cab_ride_status(
        db=db,
        ride=ride,
        new_status="CANCELLED",
        provider_status="cancelled",
        note=data.reason,
        cancellation_reason=data.reason,
    )
    logger.info("Ride cancelled: ride_id=%d user=%d reason=%s", ride_id, user_id, data.reason)
    return updated_ride


@router.post(
    "/{ride_id}/status",
    response_model=schemas.CabRideResponse,
    summary="[DEBUG] Force a status transition",
    include_in_schema=True,   # set False in production
)
def force_status(
    ride_id: int,
    new_status: str = Query(..., description="New status to set"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Development-only endpoint: manually advance a ride through its lifecycle.
    Useful for testing the Flutter UI status flow without a real provider.

    Example: CONFIRMED → ARRIVING → IN_PROGRESS → COMPLETED
    """
    if new_status.upper() not in _VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid: {sorted(_VALID_STATUSES)}",
        )

    ride = crud.get_cab_ride(db, ride_id=ride_id, user_id=user_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    updated_ride = crud.update_cab_ride_status(
        db=db,
        ride=ride,
        new_status=new_status.upper(),
        note=f"[DEBUG] Status manually set to {new_status.upper()}",
    )
    return updated_ride
