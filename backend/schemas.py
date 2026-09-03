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

class WalletResponse(BaseModel):
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

<<<<<<< HEAD

# ─────────────────────────────────────────────
#  Travel History Schemas
# ─────────────────────────────────────────────

class UserTripLegCreate(BaseModel):
    sequence: int = 1
    transport_mode: str = "other"
    origin: str
    destination: str
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    distance_km: Optional[float] = 0.0
    duration_minutes: Optional[int] = 0
    fare: Optional[float] = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    route_name: Optional[str] = None
    operator_name: Optional[str] = None
    ticket_reference: Optional[str] = None


class UserTripLegResponse(BaseModel):
    id: int
    trip_id: int
    sequence: int
    transport_mode: str
    origin: str
    destination: str
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    distance_km: Optional[float] = None
    duration_minutes: Optional[int] = None
    fare: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    route_name: Optional[str] = None
    operator_name: Optional[str] = None
    ticket_reference: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserTripCreate(BaseModel):
    origin: str
    destination: str
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    transport_mode: Optional[str] = "other"
    total_distance_km: Optional[float] = 0.0
    total_duration_minutes: Optional[int] = 0
    total_fare: Optional[float] = 0.0
    currency: Optional[str] = "INR"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    route_name: Optional[str] = None
    operator_name: Optional[str] = None
    ticket_reference: Optional[str] = None
    num_transfers: Optional[int] = 0
    status: Optional[str] = "completed"
    legs: Optional[List[UserTripLegCreate]] = None


class UserTripUpdate(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    transport_mode: Optional[str] = None
    total_distance_km: Optional[float] = None
    total_duration_minutes: Optional[int] = None
    total_fare: Optional[float] = None
    currency: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    route_name: Optional[str] = None
    operator_name: Optional[str] = None
    ticket_reference: Optional[str] = None
    num_transfers: Optional[int] = None
    status: Optional[str] = None


class UserTripResponse(BaseModel):
    id: int
    user_id: int
    booking_id: Optional[int] = None
    origin: str
    destination: str
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    transport_mode: Optional[str] = None
    total_distance_km: Optional[float] = None
    total_duration_minutes: Optional[int] = None
    total_fare: Optional[float] = None
    currency: Optional[str] = "INR"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    route_name: Optional[str] = None
    operator_name: Optional[str] = None
    ticket_reference: Optional[str] = None
    num_transfers: Optional[int] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    legs: List[UserTripLegResponse] = []

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
#  Statistics Schemas
# ─────────────────────────────────────────────

class TransportModeStats(BaseModel):
    transport_mode: str
    trip_count: int
    total_distance_km: float
    total_duration_minutes: int
    total_fare: float


class WeeklyStats(BaseModel):
    week_start: str   # ISO date string (Monday)
    trip_count: int
    total_distance_km: float
    total_fare: float


class MonthlyStats(BaseModel):
    month: str        # "2026-08" format
    trip_count: int
    total_distance_km: float
    total_fare: float


class GreenTravelStats(BaseModel):
    total_co2_kg: float                          # estimated emissions
    co2_saved_vs_car_kg: float                   # savings compared to driving
    public_transport_distance_km: float
    walking_distance_km: float
    greenest_mode: Optional[str] = None
    note: str = "Estimated values based on standard emission factors"


class TravelStatsOverview(BaseModel):
    total_trips: int
    total_distance_km: float
    total_duration_minutes: int
    total_fare: float
    average_distance_km: float
    average_duration_minutes: float
    most_used_mode: Optional[str] = None
    by_mode: List[TransportModeStats] = []
    weekly: List[WeeklyStats] = []
    monthly: List[MonthlyStats] = []
    green: GreenTravelStats
    period: str = "all_time"


# ─────────────────────────────────────────────────────────────────────────────
#  Ride-Booking Schemas (cab / on-demand rides)
# ─────────────────────────────────────────────────────────────────────────────

class RideProductResponse(BaseModel):
    """A single ride type offered by the active provider."""
    product_id: str
    name: str
    description: str
    icon: str
    capacity: int
    currency: str
    estimated_fare_min: float
    estimated_fare_max: float
    estimated_fare: float
    estimated_duration_minutes: int
    estimated_distance_km: float


class RideProductsRequest(BaseModel):
    """Request body for GET /rides/products."""
    pickup_lat: float = Field(..., ge=-90, le=90)
    pickup_lon: float = Field(..., ge=-180, le=180)
    destination_lat: float = Field(..., ge=-90, le=90)
    destination_lon: float = Field(..., ge=-180, le=180)
    pickup_address: str = Field(..., min_length=1, max_length=500)
    destination_address: str = Field(..., min_length=1, max_length=500)
    provider: str = Field(default="mock", description="Provider slug, e.g. 'mock', 'uber'")


class RideProductsResponse(BaseModel):
    """Response for the products/estimate list endpoint."""
    provider: str
    distance_km: float
    duration_minutes: int
    routing_source: str           # "ors" | "haversine"
    products: List[RideProductResponse]


class RideBookRequest(BaseModel):
    """Request body for POST /rides/book."""
    product_id: str = Field(..., description="e.g. 'mock_economy'")
    pickup_lat: float = Field(..., ge=-90, le=90)
    pickup_lon: float = Field(..., ge=-180, le=180)
    pickup_address: str = Field(..., min_length=1, max_length=500)
    destination_lat: float = Field(..., ge=-90, le=90)
    destination_lon: float = Field(..., ge=-180, le=180)
    destination_address: str = Field(..., min_length=1, max_length=500)
    payment_method: Optional[str] = Field(
        default="cash",
        description="cash | card | upi | wallet",
    )
    provider: str = Field(default="mock")


class RideStatusHistoryItem(BaseModel):
    status: str
    provider_status: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
=======
# ---------------------------------------------------------------------------
# Transit search schemas (Source → Destination)
# ---------------------------------------------------------------------------

class StopSearchResult(BaseModel):
    """One stop returned by GET /search/stops."""
    id: int
    stop_code: str
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    mode: Optional[str] = None
    operator_id: Optional[int] = None
>>>>>>> bdc85f0 (Trains fetched from db on search button)

    class Config:
        from_attributes = True


<<<<<<< HEAD
class CabRideResponse(BaseModel):
    """Full ride detail returned to the Flutter client."""
    id: int
    provider: str
    provider_ride_id: Optional[str] = None
    status: str

    pickup_lat: float
    pickup_lon: float
    pickup_address: str
    destination_lat: float
    destination_lon: float
    destination_address: str

    ride_type: str
    ride_type_name: Optional[str] = None
    ride_type_icon: Optional[str] = None

    estimated_fare_min: Optional[float] = None
    estimated_fare_max: Optional[float] = None
    estimated_fare: Optional[float] = None
    currency: str
    estimated_distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None

    actual_fare: Optional[float] = None
    actual_distance_km: Optional[float] = None
    actual_duration_minutes: Optional[int] = None

    payment_method: Optional[str] = None
    cancellation_reason: Optional[str] = None

    requested_at: datetime
    confirmed_at: Optional[datetime] = None
    arriving_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime

    status_history: List[RideStatusHistoryItem] = []

    class Config:
        from_attributes = True


class RideCancelRequest(BaseModel):
    reason: Optional[str] = Field(
        default="Cancelled by user",
        max_length=500,
    )

=======
class TripSearchRequest(BaseModel):
    """POST /search/trips request body."""
    source_stop_id: int
    destination_stop_id: int
    mode: Optional[str] = None   # "train" | "bus" | None (any)


class TripStopInfo(BaseModel):
    """Snapshot of a stop inside a search result."""
    stop_id: int
    stop_code: str
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    arrival_time: str
    departure_time: str
    stop_sequence: int


class TripSearchResult(BaseModel):
    """One matching trip returned by POST /search/trips."""
    trip_id: int
    trip_code: str
    trip_name: str              # trip_short_name (e.g. "99001 Thane - Panvel Local 1")
    direction: Optional[str]    # "DN" | "UP" | ""
    route_id: int
    route_code: str
    route_name: str
    mode: str
    operator_id: Optional[int]
    operator_name: Optional[str]
    source: TripStopInfo
    destination: TripStopInfo


class TripSearchResponse(BaseModel):
    """Wrapper returned by POST /search/trips."""
    success: bool
    message: str
    results: List[TripSearchResult]
>>>>>>> bdc85f0 (Trains fetched from db on search button)
