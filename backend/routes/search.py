"""
routes/search.py
================
WAY TRANSIT — Search API

Endpoints
---------
GET  /search/stops               — autocomplete station names (all modes)
GET  /search/route/{id}          — single route detail
GET  /search/route/{id}/path     — lat/lon path for map visualisation
POST /search/trips               — source → destination trip search (train/bus/any)
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, text
from sqlalchemy.orm import Session, aliased

import models
import schemas
from database import SessionLocal

log = logging.getLogger("way_transit")

router = APIRouter(prefix="/search", tags=["search"])


# ---------------------------------------------------------------------------
# DB dependency (local to this router, consistent with existing pattern)
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /search/stops?q=<query>&mode=<optional>
# ---------------------------------------------------------------------------
@router.get("/stops", response_model=List[schemas.StopSearchResult])
def search_stops(
    q: str = "",
    mode: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """
    Case-insensitive partial station-name search.
    Used by Flutter autocomplete fields.
    Returns stop_id, stop_code, name, lat, lon, mode, operator_id.
    """
    q = (q or "").strip()
    if not q:
        return []

    query = (
        db.query(models.Stop)
        .filter(models.Stop.name.ilike(f"%{q}%"))
        .filter(models.Stop.is_active == True)   # noqa: E712
    )
    if mode:
        query = query.filter(models.Stop.mode == mode.lower())

    # Sort: train first, then metro, then bus — so rail stops surface before
    # the many bus stops that share similar names (e.g. "CSMT", "Kalyan").
    from sqlalchemy import case
    mode_order = case(
        (models.Stop.mode == "train", 0),
        (models.Stop.mode == "metro", 1),
        else_=2,
    )
    stops = query.order_by(mode_order, models.Stop.name).limit(max(1, min(limit, 50))).all()

    return [
        schemas.StopSearchResult(
            id=s.id,
            stop_code=s.stop_code or "",
            name=s.name,
            lat=s.lat,
            lon=s.lon,
            mode=s.mode,
            operator_id=s.operator_id,
        )
        for s in stops
    ]


# ---------------------------------------------------------------------------
# POST /search/trips
# ---------------------------------------------------------------------------
@router.post("/trips", response_model=schemas.TripSearchResponse)
def search_trips(
    body: schemas.TripSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Find all direct trips between source_stop_id and destination_stop_id
    where source stop_sequence < destination stop_sequence.

    Uses existing tables: stops / routes / trips / stop_times.
    No new tables. Works for train, bus, and any future mode.
    """
    src_id  = body.source_stop_id
    dst_id  = body.destination_stop_id
    mode    = (body.mode or "").strip().lower() or None

    # ── Basic validation ──────────────────────────────────────────────────
    if src_id == dst_id:
        raise HTTPException(
            status_code=400,
            detail="Source and destination cannot be the same station.",
        )

    src_stop = db.query(models.Stop).filter(models.Stop.id == src_id).first()
    if not src_stop:
        raise HTTPException(status_code=404, detail=f"Source stop id={src_id} not found.")

    dst_stop = db.query(models.Stop).filter(models.Stop.id == dst_id).first()
    if not dst_stop:
        raise HTTPException(status_code=404, detail=f"Destination stop id={dst_id} not found.")

    # Mode compatibility: if both stops have a mode, they must match
    if src_stop.mode and dst_stop.mode and src_stop.mode != dst_stop.mode:
        return schemas.TripSearchResponse(
            success=True,
            results=[],
            message=(
                f"Source is a {src_stop.mode} stop but destination is a "
                f"{dst_stop.mode} stop. No direct service possible."
            ),
        )

    # Resolve effective mode for the filter
    effective_mode = mode or src_stop.mode or dst_stop.mode

    # ── Core query ────────────────────────────────────────────────────────
    #
    # Logic:
    #   st_src  = stop_times row for the source stop
    #   st_dst  = stop_times row for the destination stop
    #   Both must belong to the SAME trip.
    #   st_src.stop_sequence < st_dst.stop_sequence  (direction check)
    #   JOIN to trips → routes for metadata.
    #
    StopTimeSrc = aliased(models.StopTime, name="st_src")
    StopTimeDst = aliased(models.StopTime, name="st_dst")

    q = (
        db.query(
            models.Trip,
            StopTimeSrc,
            StopTimeDst,
        )
        .join(StopTimeSrc, StopTimeSrc.trip_id == models.Trip.id)
        .join(StopTimeDst, StopTimeDst.trip_id == models.Trip.id)
        .join(models.Route, models.Route.id == models.Trip.route_id)
        .filter(
            StopTimeSrc.stop_id == src_id,
            StopTimeDst.stop_id == dst_id,
            StopTimeSrc.stop_sequence < StopTimeDst.stop_sequence,
        )
    )

    if effective_mode:
        q = q.filter(models.Route.mode == effective_mode)

    # Order by departure time at source (string HH:MM sorts correctly)
    q = q.order_by(StopTimeSrc.departure_time)

    rows = q.all()

    if not rows:
        src_name = src_stop.name
        dst_name = dst_stop.name
        return schemas.TripSearchResponse(
            success=True,
            results=[],
            message=f"No direct train found between {src_name} and {dst_name}.",
        )

    # ── Build results (deduplicate by trip_id) ────────────────────────────
    seen_trip_ids: set[int] = set()
    results: List[schemas.TripSearchResult] = []

    # Pre-fetch operators in one query to avoid N+1
    route_ids  = {row[0].route_id for row in rows}
    route_map  = {r.id: r for r in db.query(models.Route).filter(models.Route.id.in_(route_ids)).all()}
    op_ids     = {r.operator_id for r in route_map.values() if r.operator_id}
    op_map     = {o.id: o for o in db.query(models.Operator).filter(models.Operator.id.in_(op_ids)).all()}

    for trip, st_src, st_dst in rows:
        if trip.id in seen_trip_ids:
            continue
        seen_trip_ids.add(trip.id)

        route    = route_map.get(trip.route_id)
        operator = op_map.get(route.operator_id) if route and route.operator_id else None

        results.append(
            schemas.TripSearchResult(
                trip_id=trip.id,
                trip_code=trip.trip_code or "",
                trip_name=trip.trip_short_name or trip.trip_code or "",
                direction=trip.direction or "",
                route_id=route.id if route else trip.route_id,
                route_code=route.route_code if route else "",
                route_name=route.name if route else "",
                mode=route.mode if route else (effective_mode or ""),
                operator_id=operator.id if operator else None,
                operator_name=operator.name if operator else None,
                source=schemas.TripStopInfo(
                    stop_id=src_stop.id,
                    stop_code=src_stop.stop_code or "",
                    name=src_stop.name,
                    lat=src_stop.lat,
                    lon=src_stop.lon,
                    arrival_time=st_src.arrival_time,
                    departure_time=st_src.departure_time,
                    stop_sequence=st_src.stop_sequence,
                ),
                destination=schemas.TripStopInfo(
                    stop_id=dst_stop.id,
                    stop_code=dst_stop.stop_code or "",
                    name=dst_stop.name,
                    lat=dst_stop.lat,
                    lon=dst_stop.lon,
                    arrival_time=st_dst.arrival_time,
                    departure_time=st_dst.departure_time,
                    stop_sequence=st_dst.stop_sequence,
                ),
            )
        )

    return schemas.TripSearchResponse(
        success=True,
        results=results,
        message=f"{len(results)} service(s) found.",
    )


# ---------------------------------------------------------------------------
# GET /search/routes  (legacy — kept for backwards compat with old Flutter code)
# ---------------------------------------------------------------------------
@router.get("/routes", response_model=list[schemas.RouteResponse])
def search_routes(source: str, destination: str, db: Session = Depends(get_db)):
    """Legacy endpoint. Prefer POST /search/trips for full timetable data."""
    import crud
    return crud.get_routes(db, source, destination)


# ---------------------------------------------------------------------------
# GET /search/route/{route_id}
# ---------------------------------------------------------------------------
@router.get("/route/{route_id}", response_model=schemas.RouteResponse)
def get_route(route_id: int, db: Session = Depends(get_db)):
    route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


# ---------------------------------------------------------------------------
# GET /search/route/{route_id}/path
# ---------------------------------------------------------------------------
@router.get("/route/{route_id}/path", response_model=schemas.MapRoutePathResponse)
def get_route_path(route_id: int, db: Session = Depends(get_db)):
    """Return the lat/lon path of a route for map visualisation."""
    route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    trip = db.query(models.Trip).filter(models.Trip.route_id == route.id).first()
    if not trip:
        return schemas.MapRoutePathResponse(route_id=route.id, mode=route.mode, stops=[])

    stop_times = (
        db.query(models.StopTime)
        .filter(models.StopTime.trip_id == trip.id)
        .order_by(models.StopTime.stop_sequence)
        .all()
    )

    stops_response = []
    for st in stop_times:
        stop = db.query(models.Stop).filter(models.Stop.id == st.stop_id).first()
        if stop:
            stops_response.append(
                schemas.MapStopResponse(
                    id=stop.id,
                    name=stop.name,
                    lat=stop.lat,
                    lon=stop.lon,
                    mode=stop.mode,
                    sequence=st.stop_sequence,
                )
            )

    return schemas.MapRoutePathResponse(
        route_id=route.id,
        mode=route.mode,
        stops=stops_response,
    )
