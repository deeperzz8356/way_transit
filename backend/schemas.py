from pydantic import BaseModel, model_validator, Field
from typing import Optional, Any, List
from datetime import datetime, date

from platform_colors import color_for_mode, normalize_mode, MODE_LABELS


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
    ticket_number: Optional[str] = None
    qr_payload: Optional[str] = None
    mode: Optional[str] = None
    operator_name: Optional[str] = None
    operator: Optional[str] = None  # alias
    travel_date: Optional[str] = None
    class_name: Optional[str] = None
    fare: Optional[float] = None
    source_type: Optional[str] = "manual"
    ticket_trip_id: Optional[int] = None

class TicketConfirmRequest(BaseModel):
    source: str
    destination: str
    operator: Optional[str] = None
    operator_name: Optional[str] = None
    travel_date: Optional[str] = None
    ticket_number: Optional[str] = None
    qr_payload: Optional[str] = None
    mode: Optional[str] = None
    class_name: Optional[str] = None
    fare: Optional[float] = None
    ticket_trip_id: Optional[int] = None

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
    ticket_number: Optional[str] = None
    qr_payload: Optional[str] = None
    mode: Optional[str] = None
    mode_label: Optional[str] = None
    color_hex: Optional[str] = None
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    class_name: Optional[str] = None
    fare: Optional[float] = None
    source_type: Optional[str] = None
    travel_date: Optional[date] = None
    journey_started_at: Optional[datetime] = None
    journey_estimated_end_at: Optional[datetime] = None
    is_active: bool = False
    distance_km: Optional[float] = None
    booked_at: Optional[datetime] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    qr_display: Optional[str] = None
    ticket_trip_id: Optional[int] = None
    route: Optional[RouteResponse] = None
    
    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def populate_source_destination(cls, data: Any):
        if isinstance(data, dict):
            mode = normalize_mode(data.get("mode"))
            op_color = data.get("color_hex")
            data = dict(data)
            data["mode"] = mode
            data["mode_label"] = MODE_LABELS.get(mode, "Other")
            data["color_hex"] = color_for_mode(mode, op_color)
            data["qr_display"] = (
                data.get("qr_payload")
                or data.get("ticket_number")
                or data.get("ticket_code")
            )
            data["is_active"] = str(data.get("status", "")).upper() == "IN_PROGRESS"
            return data
        source = getattr(data, "source", None)
        destination = getattr(data, "destination", None)
        route = getattr(data, "route", None)
        if not source and route is not None:
            source = getattr(route, "source", None)
        if not destination and route is not None:
            destination = getattr(route, "destination", None)
        mode = normalize_mode(getattr(data, "mode", None))
        operator = getattr(data, "operator", None)
        op_color = getattr(operator, "color_hex", None) if operator is not None else None
        ticket_number = getattr(data, "ticket_number", None)
        qr_payload = getattr(data, "qr_payload", None)
        ticket_code = getattr(data, "ticket_code", None)
        status = getattr(data, "status", None)
        return {
            "id": data.id,
            "user_id": data.user_id,
            "route_id": data.route_id,
            "status": status,
            "image_url": data.image_url,
            "ticket_code": ticket_code,
            "ticket_number": ticket_number,
            "qr_payload": qr_payload,
            "mode": mode,
            "mode_label": MODE_LABELS.get(mode, "Other"),
            "color_hex": color_for_mode(mode, op_color),
            "operator_id": getattr(data, "operator_id", None),
            "operator_name": getattr(data, "operator_name", None),
            "class_name": getattr(data, "class_name", None),
            "fare": getattr(data, "fare", None),
            "source_type": getattr(data, "source_type", None),
            "travel_date": getattr(data, "travel_date", None),
            "journey_started_at": getattr(data, "journey_started_at", None),
            "journey_estimated_end_at": getattr(data, "journey_estimated_end_at", None),
            "is_active": str(status or "").upper() == "IN_PROGRESS",
            "distance_km": data.distance_km,
            "booked_at": data.booked_at,
            "source": source,
            "destination": destination,
            "qr_display": qr_payload or ticket_number or ticket_code,
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
    ticket_number: Optional[str] = None
    qr_payload: Optional[str] = None
    mode: Optional[str] = None
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

class JourneyStartRequest(BaseModel):
    start_time: Optional[str] = None  # ISO datetime
    estimated_end_time: Optional[str] = None  # ISO datetime
    make_active: bool = True  # demote other active journeys

class JourneyResponse(BaseModel):
    id: int
    user_id: int
    booking_id: Optional[int] = None
    from_stop_id: Optional[int] = None
    to_stop_id: Optional[int] = None
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    estimated_end_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    mode: Optional[str] = None
    color_hex: Optional[str] = None
    is_active: bool = False

    class Config:
        from_attributes = True

class UserPassResponse(BaseModel):
    id: int
    pass_id: int
    name: Optional[str] = None
    mode_coverage: Optional[str] = None
    color_hex: Optional[str] = None
    valid_until: Optional[datetime] = None
    status: str
    price: Optional[float] = None

    class Config:
        from_attributes = True

class TicketTripCreate(BaseModel):
    name: str
    notes: Optional[str] = None
    travel_date: Optional[str] = None

class TicketTripUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    travel_date: Optional[str] = None

class TicketTripTicketsRequest(BaseModel):
    ticket_ids: List[int] = Field(default_factory=list)

class TicketTripResponse(BaseModel):
    id: int
    user_id: int
    name: str
    notes: Optional[str] = None
    travel_date: Optional[date] = None
    ticket_count: int = 0
    tickets: List[BookingResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def populate_ticket_count(cls, data: Any):
        if isinstance(data, dict):
            tickets = data.get("tickets") or []
            data = dict(data)
            data["ticket_count"] = data.get("ticket_count")
            if data["ticket_count"] is None:
                data["ticket_count"] = len(tickets)
            return data
        tickets = getattr(data, "tickets", None) or []
        # Attach computed count for ORM objects
        try:
            data.ticket_count = len(tickets)
        except Exception:
            pass
        return data

class WalletResponse(BaseModel):
    trips: List[TicketTripResponse] = Field(default_factory=list)
    tickets: List[BookingResponse] = Field(default_factory=list)
    passes: List[UserPassResponse] = Field(default_factory=list)

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
