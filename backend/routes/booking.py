from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
import schemas
import models
from dependencies import get_current_user

router = APIRouter(prefix="/booking", tags=["booking"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/book", response_model=schemas.BookingResponse)
def book(
    data: schemas.BookingCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Book a route (requires auth token)"""
    # validate route exists
    route = db.query(models.Route).filter(models.Route.id == data.route_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Check for duplicate booking
    existing_booking = db.query(models.Booking).filter(
        models.Booking.user_id == user_id,
        models.Booking.route_id == data.route_id
    ).first()
    
    if existing_booking:
        raise HTTPException(status_code=400, detail="Already booked this route")

    return crud.create_booking(db, user_id, data.route_id)

@router.get("/my-bookings", response_model=list[schemas.BookingResponse])
def get_my_bookings(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bookings for current user (requires auth token)"""
    return db.query(models.Booking).filter(models.Booking.user_id == user_id).all()