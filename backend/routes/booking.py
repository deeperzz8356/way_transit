from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
import schemas
import models
from dependencies import get_current_user
import razorpay
import hmac
import hashlib
import os
import time
from dotenv import load_dotenv

load_dotenv()
RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")

router = APIRouter(prefix="/booking", tags=["booking"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if RAZORPAY_KEY and RAZORPAY_SECRET:
    client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
else:
    client = None

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

@router.post("/create-order")
def create_order(
    data: schemas.BookingCreateOrder,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Razorpay order for booking"""
    if not client:
        raise HTTPException(status_code=500, detail="Razorpay not configured")

    fare = round(10 + (2 * data.distance_km))
    receipt_id = f"receipt_{user_id}_{int(time.time())}"
    
    order_data = {
        "amount": fare * 100,
        "currency": "INR",
        "receipt": receipt_id
    }
    
    try:
        # Some SDK versions use order.create, some use orders.create
        if hasattr(client, 'order'):
            razorpay_order = client.order.create(data=order_data)
        else:
            razorpay_order = client.orders.create(order_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")
        
    order_id = razorpay_order['id']
    
    booking = crud.create_booking_order(
        db, 
        user_id, 
        data.route_id, 
        data.source, 
        data.destination, 
        data.distance_km, 
        fare, 
        order_id
    )
    
    return {
        "order_id": order_id,
        "amount": fare * 100,
        "currency": "INR",
        "booking_id": booking.id,
        "razorpay_key": RAZORPAY_KEY
    }

@router.post("/verify-payment")
def verify_payment(
    data: schemas.PaymentVerify,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        msg = f"{data.razorpay_order_id}|{data.razorpay_payment_id}"
        expected_signature = hmac.new(
            RAZORPAY_SECRET.encode('utf-8'),
            msg.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        booking = db.query(models.Booking).filter(models.Booking.id == data.booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        if expected_signature == data.razorpay_signature:
            booking.payment_status = "confirmed"
            booking.payment_id = data.razorpay_payment_id
            booking.status = "CONFIRMED"
            db.commit()
            return {"status": "success", "booking_id": booking.id, "message": "Payment verified successfully"}
        else:
            booking.payment_status = "failed"
            booking.status = "FAILED"
            db.commit()
            raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/my-bookings", response_model=list[schemas.BookingResponse])
def get_my_bookings(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bookings for current user (requires auth token)"""
    return db.query(models.Booking).filter(
        models.Booking.user_id == user_id
    ).order_by(models.Booking.booked_at.desc()).all()