from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    
    class Config:
        from_attributes = True

class RouteCreate(BaseModel):
    source: str
    destination: str
    transport: str
    departure_time: str
    arrival_time: str
    price: int

class RouteResponse(BaseModel):
    id: int
    source: str
    destination: str
    transport: str
    departure_time: str
    arrival_time: str
    price: int
    
    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    route_id: int

class BookingCreateOrder(BaseModel):
    route_id: int
    source: str
    destination: str
    distance_km: float

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    booking_id: int

class BookingResponse(BaseModel):
    id: int
    user_id: int
    route_id: int
    status: str
    created_at: datetime
    payment_status: Optional[str] = None
    payment_order_id: Optional[str] = None
    payment_id: Optional[str] = None
    fare: Optional[float] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    distance_km: Optional[float] = None
    booked_at: Optional[datetime] = None
    route: Optional[RouteResponse] = None
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str