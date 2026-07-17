from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
import schemas
import models

router = APIRouter(prefix="/search", tags=["search"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/routes", response_model=list[schemas.RouteResponse])
def search(source: str, destination: str, db: Session = Depends(get_db)):
    """Search routes by source and destination"""
    return crud.get_routes(db, source, destination)

@router.get("/route/{route_id}", response_model=schemas.RouteResponse)
def get_route(route_id: int, db: Session = Depends(get_db)):
    """Get single route details by ID"""
    route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route
@router.get("/route/{route_id}/path", response_model=schemas.MapRoutePathResponse)
def get_route_path(route_id: int, db: Session = Depends(get_db)):
    """Get the lat/lon path of a route for map visualization"""
    route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
        
    # Get a representative trip for this route
    trip = db.query(models.Trip).filter(models.Trip.route_id == route.id).first()
    if not trip:
        return schemas.MapRoutePathResponse(route_id=route.id, mode=route.mode, stops=[])
        
    # Get all stop times for this trip, ordered by sequence
    stop_times = db.query(models.StopTime).filter(
        models.StopTime.trip_id == trip.id
    ).order_by(models.StopTime.stop_sequence).all()
    
    stops_response = []
    for st in stop_times:
        stop = db.query(models.Stop).filter(models.Stop.id == st.stop_id).first()
        if stop:
            stops_response.append(schemas.MapStopResponse(
                id=stop.id,
                name=stop.name,
                lat=stop.lat,
                lon=stop.lon,
                mode=stop.mode,
                sequence=st.stop_sequence
            ))
            
    return schemas.MapRoutePathResponse(
        route_id=route.id,
        mode=route.mode,
        stops=stops_response
    )
