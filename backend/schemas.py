from pydantic import BaseModel, model_validator
from typing import Optional, Any
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

class TicketAddRequest(BaseModel):
    source: str
    destination: str
    image_url: Optional[str] = None

class TicketConfirmRequest(BaseModel):
    source: str
    destination: str
    operator: Optional[str] = None
    travel_date: Optional[str] = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class BookingResponse(BaseModel):
    id: int
    user_id: int
    route_id: Optional[int] = None
    status: str
    image_url: Optional[str] = None
    ticket_code: Optional[str] = None
    distance_km: Optional[float] = None
    booked_at: Optional[datetime] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    route: Optional[RouteResponse] = None
    
    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def populate_source_destination(cls, data: Any):
        if isinstance(data, dict):
            return data
        source = getattr(data, "source", None)
        destination = getattr(data, "destination", None)
        route = getattr(data, "route", None)
        if not source and route is not None:
            source = getattr(route, "source", None)
        if not destination and route is not None:
            destination = getattr(route, "destination", None)
        return {
            "id": data.id,
            "user_id": data.user_id,
            "route_id": data.route_id,
            "status": data.status,
            "image_url": data.image_url,
            "ticket_code": data.ticket_code,
            "distance_km": data.distance_km,
            "booked_at": data.booked_at,
            "source": source,
            "destination": destination,
            "route": route,
        }

class TicketJobResponse(BaseModel):
    id: int
    status: str
    image_url: str
    source: Optional[str] = None
    destination: Optional[str] = None
    operator: Optional[str] = None
    travel_date: Optional[str] = None
    raw_text: Optional[str] = None
    error_message: Optional[str] = None
    booking_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TicketUploadResponse(BaseModel):
    job_id: int
    status: str
    image_url: str
    events_url: str

class PhoneRequest(BaseModel):
    phone: str

class OtpVerifyRequest(BaseModel):
    phone: str
    otp: str

class GoogleAuthRequest(BaseModel):
    id_token: str

class FirebaseAuthRequest(BaseModel):
    id_token: str

class UserUpdateRequest(BaseModel):
    name: str

class MessageResponse(BaseModel):
    message: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    phone: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    google_id: Optional[str] = None
    profile_image: Optional[str] = None
    auth_provider: Optional[str] = None
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MapStopResponse(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    mode: str
    sequence: int

class MapRoutePathResponse(BaseModel):
    route_id: int
    mode: str
    stops: list[MapStopResponse]
