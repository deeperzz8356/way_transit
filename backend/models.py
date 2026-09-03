from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, Date, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    state = Column(String)
    country = Column(String)
    center_lat = Column(Float)
    center_lon = Column(Float)
    is_active = Column(Boolean, default=True)

    operators = relationship("Operator", back_populates="city")
    stops = relationship("Stop", back_populates="city")
    routes = relationship("Route", back_populates="city")
    alerts = relationship("Alert", back_populates="city")

class Operator(Base):
    __tablename__ = "operators"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), index=True)
    name = Column(String, nullable=False)
    short_name = Column(String)
    mode = Column(String)
    color_hex = Column(String)
    is_active = Column(Boolean, default=True)

    city = relationship("City", back_populates="operators")
    stops = relationship("Stop", back_populates="operator")
    routes = relationship("Route", back_populates="operator")
    fare_rules = relationship("FareRule", back_populates="operator")
    passes = relationship("Pass", back_populates="operator")
    concessions = relationship("Concession", back_populates="operator")

class Stop(Base):
    __tablename__ = "stops"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), index=True)
    stop_code = Column(String, index=True)
    name = Column(String, nullable=False)
    name_local = Column(String)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    mode = Column(String)
    is_interchange = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    wheelchair = Column(Boolean, default=False)
    platform_count = Column(Integer, default=1)

    city = relationship("City", back_populates="stops")
    operator = relationship("Operator", back_populates="stops")
    stop_times = relationship("StopTime", back_populates="stop")
    departure_bookings = relationship("Booking", foreign_keys="[Booking.from_stop_id]", back_populates="departure_stop")
    arrival_bookings = relationship("Booking", foreign_keys="[Booking.to_stop_id]", back_populates="arrival_stop")
    saved_places = relationship("SavedPlace", back_populates="stop")
    journey_origins = relationship("Journey", foreign_keys="[Journey.from_stop_id]", back_populates="origin_stop")
    journey_destinations = relationship("Journey", foreign_keys="[Journey.to_stop_id]", back_populates="destination_stop")

class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), index=True)
    route_code = Column(String, index=True)
    name = Column(String, nullable=False)
    mode = Column(String)
    color_hex = Column(String)
    is_active = Column(Boolean, default=True)

    city = relationship("City", back_populates="routes")
    operator = relationship("Operator", back_populates="routes")
    trips = relationship("Trip", back_populates="route")
    shapes = relationship("Shape", back_populates="route")
    alerts = relationship("Alert", back_populates="route")
    vehicle_positions = relationship("VehiclePosition", back_populates="route")
    bookings = relationship("Booking", back_populates="route")

    @property
    def source(self) -> str:
        if self.trips and self.trips[0].stop_times:
            sorted_stops = sorted(self.trips[0].stop_times, key=lambda x: x.stop_sequence)
            return sorted_stops[0].stop.name
        if self.name and " to " in self.name.lower():
            parts = self.name.split(" to ", 1)
            if len(parts) == 2 and parts[0].strip():
                return parts[0].strip()
        return "Unknown"

    @property
    def destination(self) -> str:
        if self.trips and self.trips[0].stop_times:
            sorted_stops = sorted(self.trips[0].stop_times, key=lambda x: x.stop_sequence)
            return sorted_stops[-1].stop.name
        if self.name and " to " in self.name.lower():
            parts = self.name.split(" to ", 1)
            if len(parts) == 2 and parts[1].strip():
                return parts[1].strip()
        return "Unknown"

    @property
    def transport(self) -> str:
        return self.mode or "bus"

    @property
    def departure_time(self) -> str:
        if self.trips and self.trips[0].stop_times:
            sorted_stops = sorted(self.trips[0].stop_times, key=lambda x: x.stop_sequence)
            return sorted_stops[0].departure_time
        return "08:00 AM"

    @property
    def arrival_time(self) -> str:
        if self.trips and self.trips[0].stop_times:
            sorted_stops = sorted(self.trips[0].stop_times, key=lambda x: x.stop_sequence)
            return sorted_stops[-1].arrival_time
        return "09:00 AM"

    @property
    def price(self) -> int:
        return 100

class Shape(Base):
    __tablename__ = "shapes"
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    sequence = Column(Integer, nullable=False)

    route = relationship("Route", back_populates="shapes")

class ServiceCalendar(Base):
    __tablename__ = "service_calendar"
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String, unique=True, index=True)
    monday = Column(Boolean, default=True)
    tuesday = Column(Boolean, default=True)
    wednesday = Column(Boolean, default=True)
    thursday = Column(Boolean, default=True)
    friday = Column(Boolean, default=True)
    saturday = Column(Boolean, default=True)
    sunday = Column(Boolean, default=True)
    start_date = Column(Date)
    end_date = Column(Date)

    trips = relationship("Trip", back_populates="service")
    exceptions = relationship("CalendarException", back_populates="service")

class CalendarException(Base):
    __tablename__ = "calendar_exceptions"
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String, ForeignKey("service_calendar.service_id"), index=True)
    exception_date = Column(Date, nullable=False)
    exception_type = Column(Integer, nullable=False)

    service = relationship("ServiceCalendar", back_populates="exceptions")

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True)
    service_id = Column(String, ForeignKey("service_calendar.service_id"), index=True)
    shape_id = Column(Integer, ForeignKey("shapes.id"), nullable=True)
    direction = Column(String)
    trip_short_name = Column(String)
    trip_code = Column(String, index=True)

    route = relationship("Route", back_populates="trips")
    service = relationship("ServiceCalendar", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip")
    vehicle_positions = relationship("VehiclePosition", back_populates="trip")
    bookings = relationship("Booking", back_populates="trip")

class StopTime(Base):
    __tablename__ = "stop_times"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), index=True)
    stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    stop_sequence = Column(Integer, nullable=False)
    arrival_time = Column(String, nullable=False)
    departure_time = Column(String, nullable=False)
    pickup_type = Column(Integer, default=0)
    drop_type = Column(Integer, default=0)

    trip = relationship("Trip", back_populates="stop_times")
    stop = relationship("Stop", back_populates="stop_times")

class Transfer(Base):
    __tablename__ = "transfers"
    id = Column(Integer, primary_key=True, index=True)
    from_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    to_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    transfer_type = Column(Integer, default=0)
    min_transfer_time = Column(Integer)
    walk_distance_m = Column(Integer)

    from_stop = relationship("Stop", foreign_keys=[from_stop_id])
    to_stop = relationship("Stop", foreign_keys=[to_stop_id])

class FareRule(Base):
    __tablename__ = "fare_rules"
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), index=True)
    rule_type = Column(String)
    base_fare = Column(Float)
    per_km_rate = Column(Float)

    operator = relationship("Operator", back_populates="fare_rules")

class FareMatrix(Base):
    __tablename__ = "fare_matrix"
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), index=True)
    from_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    to_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    price = Column(Float, nullable=False)

    operator = relationship("Operator")
    from_stop = relationship("Stop", foreign_keys=[from_stop_id])
    to_stop = relationship("Stop", foreign_keys=[to_stop_id])

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    profile_image = Column(String, nullable=True)
    auth_provider = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = relationship("Booking", back_populates="user")
    journeys = relationship("Journey", back_populates="user")
    saved_places = relationship("SavedPlace", back_populates="user")
    reward_points = relationship("RewardPoint", back_populates="user")
    wallet = relationship("Wallet", uselist=False, back_populates="user")
    user_trips = relationship("UserTrip", back_populates="user")
    cab_rides = relationship("CabRide", back_populates="user", order_by="CabRide.created_at.desc()")

class OTPCode(Base):
    __tablename__ = "otp_codes"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    hashed_code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_sent_at = Column(DateTime, default=datetime.utcnow)
    first_requested_at = Column(DateTime, default=datetime.utcnow)
    request_count = Column(Integer, default=1)
    failed_attempts = Column(Integer, default=0)

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    balance = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="wallet")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True, nullable=True)
    from_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    to_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), index=True)
    distance_km = Column(Float)
    image_url = Column(String, nullable=True)
    ticket_code = Column(String, unique=True, index=True)
    ticket_number = Column(String, nullable=True, index=True)
    qr_payload = Column(String, nullable=True)
    mode = Column(String, nullable=True, default="other")  # rail|metro|bus|cab|other
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=True, index=True)
    operator_name = Column(String, nullable=True)
    class_name = Column(String, nullable=True)
    fare = Column(Float, nullable=True)
    source_type = Column(String, nullable=True)  # scan|manual|booked
    source = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    travel_date = Column(Date)
    status = Column(String, default="CONFIRMED")  # CONFIRMED|IN_PROGRESS|USED|EXPIRED
    journey_started_at = Column(DateTime, nullable=True)
    journey_estimated_end_at = Column(DateTime, nullable=True)
    booked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    route = relationship("Route", back_populates="bookings")
    operator = relationship("Operator")
    departure_stop = relationship("Stop", foreign_keys=[from_stop_id], back_populates="departure_bookings")
    arrival_stop = relationship("Stop", foreign_keys=[to_stop_id], back_populates="arrival_bookings")
    trip = relationship("Trip", back_populates="bookings")
    reward_points = relationship("RewardPoint", back_populates="booking")
    journeys = relationship("Journey", back_populates="booking")


class TicketIngestJob(Base):
    __tablename__ = "ticket_ingest_jobs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    image_url = Column(String, nullable=False)
    status = Column(String, default="uploaded")  # uploaded|processing|extracted|confirmed|error
    source = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    operator = Column(String, nullable=True)
    travel_date = Column(String, nullable=True)
    ticket_number = Column(String, nullable=True)
    qr_payload = Column(String, nullable=True)
    mode = Column(String, nullable=True)
    raw_text = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Journey(Base):
    __tablename__ = "journeys"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True, index=True)
    from_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    to_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    total_fare = Column(Float)
    total_duration = Column(Integer)
    total_distance = Column(Float)
    status = Column(String, default="active")  # active|completed|superseded
    started_at = Column(DateTime, nullable=True)
    estimated_end_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="journeys")
    booking = relationship("Booking", back_populates="journeys")
    origin_stop = relationship("Stop", foreign_keys=[from_stop_id], back_populates="journey_origins")
    destination_stop = relationship("Stop", foreign_keys=[to_stop_id], back_populates="journey_destinations")

class SavedPlace(Base):
    __tablename__ = "saved_places"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    label = Column(String)
    stop_id = Column(Integer, ForeignKey("stops.id"), nullable=True, index=True)
    custom_name = Column(String)
    lat = Column(Float)
    lon = Column(Float)

    user = relationship("User", back_populates="saved_places")
    stop = relationship("Stop", back_populates="saved_places")

class VehiclePosition(Base):
    __tablename__ = "vehicle_positions"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String)
    trip_id = Column(Integer, ForeignKey("trips.id"), index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True)
    lat = Column(Float)
    lon = Column(Float)
    speed_kmh = Column(Float)
    bearing = Column(Integer)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    trip = relationship("Trip", back_populates="vehicle_positions")
    route = relationship("Route", back_populates="vehicle_positions")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True, index=True)
    stop_id = Column(Integer, ForeignKey("stops.id"), nullable=True, index=True)
    cause = Column(String)
    effect = Column(String)
    header = Column(String)
    description = Column(String)
    starts_at = Column(DateTime)
    ends_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    city = relationship("City", back_populates="alerts")
    route = relationship("Route", back_populates="alerts")

class RewardPoint(Base):
    __tablename__ = "reward_points"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), index=True)
    points_earned = Column(Integer, default=0)
    points_spent = Column(Integer, default=0)
    balance = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reward_points")
    booking = relationship("Booking", back_populates="reward_points")

class Pass(Base):
    __tablename__ = "passes"
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), index=True)
    name = Column(String)
    validity_days = Column(Integer)
    price = Column(Float)
    mode_coverage = Column(String)
    is_active = Column(Boolean, default=True)

    operator = relationship("Operator", back_populates="passes")
    user_passes = relationship("UserPass", back_populates="pass_product")


class UserPass(Base):
    __tablename__ = "user_passes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    pass_id = Column(Integer, ForeignKey("passes.id"), index=True)
    valid_until = Column(DateTime, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    pass_product = relationship("Pass", back_populates="user_passes")
    user = relationship("User")


class Concession(Base):
    __tablename__ = "concessions"
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), index=True)
    type = Column(String)
    discount_pct = Column(Float)
    requires_id = Column(Boolean, default=False)

    operator = relationship("Operator", back_populates="concessions")


# ─────────────────────────────────────────────
#  Travel History Tables
# ─────────────────────────────────────────────

class UserTrip(Base):
    """A completed or planned user journey (one or many legs)."""
    __tablename__ = "user_trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # Optional link to a booking that spawned this trip
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True, index=True)

    # Overall journey endpoints (plain text – no FK to stops required)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    origin_lat = Column(Float, nullable=True)
    origin_lon = Column(Float, nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lon = Column(Float, nullable=True)

    # Primary / dominant transport mode for this trip
    transport_mode = Column(String, nullable=True)   # walking|bus|train|metro|auto|cab|bike|car|other

    # Aggregate totals (summed from legs)
    total_distance_km = Column(Float, nullable=True, default=0.0)
    total_duration_minutes = Column(Integer, nullable=True, default=0)
    total_fare = Column(Float, nullable=True, default=0.0)
    currency = Column(String, nullable=True, default="INR")

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Extra metadata
    route_name = Column(String, nullable=True)
    operator_name = Column(String, nullable=True)
    ticket_reference = Column(String, nullable=True)
    num_transfers = Column(Integer, nullable=True, default=0)

    # Status: planned | started | completed | cancelled
    status = Column(String, nullable=False, default="completed", index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="user_trips")
    booking = relationship("Booking")
    legs = relationship("UserTripLeg", back_populates="trip", order_by="UserTripLeg.sequence", cascade="all, delete-orphan")


class UserTripLeg(Base):
    """A single transport leg within a UserTrip."""
    __tablename__ = "user_trip_legs"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("user_trips.id"), nullable=False, index=True)

    sequence = Column(Integer, nullable=False, default=1)       # order of this leg within the trip
    transport_mode = Column(String, nullable=False, default="other")

    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    origin_lat = Column(Float, nullable=True)
    origin_lon = Column(Float, nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lon = Column(Float, nullable=True)

    distance_km = Column(Float, nullable=True, default=0.0)
    duration_minutes = Column(Integer, nullable=True, default=0)
    fare = Column(Float, nullable=True, default=0.0)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    route_name = Column(String, nullable=True)
    operator_name = Column(String, nullable=True)
    ticket_reference = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    trip = relationship("UserTrip", back_populates="legs")


# ─────────────────────────────────────────────────────────────────
#  Ride-Booking Tables  (cab / on-demand rides, separate from
#  transit ticket "bookings" table above)
# ─────────────────────────────────────────────────────────────────

class RideProvider(Base):
    """
    A registered ride-booking provider (e.g. 'mock', 'uber').
    Stores metadata and whether the provider is in sandbox mode.
    The 'config' field holds JSON-serialised, provider-specific
    settings (base_url, scopes, etc.) — never store secrets here;
    use environment variables for credentials.
    """
    __tablename__ = "ride_providers"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(50), unique=True, nullable=False, index=True)
    # e.g. "mock", "uber", "ola", "rapido"
    display_name = Column(String(100), nullable=False)
    # e.g. "Mock Provider (Demo)", "Uber"
    is_active   = Column(Boolean, default=True, nullable=False)
    is_sandbox  = Column(Boolean, default=True,  nullable=False)
    # JSON string — non-sensitive config only
    config      = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cab_rides = relationship("CabRide", back_populates="provider_ref")


class CabRide(Base):
    """
    A single on-demand cab/ride-booking transaction.
    Completely separate from the transit 'bookings' table.

    Status lifecycle (internal):
        REQUESTED → CONFIRMED → ARRIVING → IN_PROGRESS
                                         → COMPLETED
                                         → CANCELLED
                 → FAILED  (if provider rejected the request)

    provider_ride_id: the external ID returned by the provider
    (None until the provider confirms the booking).
    """
    __tablename__ = "cab_rides"

    id   = Column(Integer, primary_key=True, index=True)

    # ── Relations ───────────────────────────────────────────────
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("ride_providers.id"), nullable=False, index=True)

    # ── Provider reference ───────────────────────────────────────
    # Internal provider slug kept as a denormalised column so we
    # can query by provider name without a join.
    provider    = Column(String(50), nullable=False, index=True)  # "mock", "uber"
    provider_ride_id = Column(String(255), nullable=True, index=True)
    # Raw status string from the external provider
    provider_status  = Column(String(100), nullable=True)

    # ── Pickup ───────────────────────────────────────────────────
    pickup_lat     = Column(Float, nullable=False)
    pickup_lon     = Column(Float, nullable=False)
    pickup_address = Column(String(500), nullable=False)

    # ── Destination ──────────────────────────────────────────────
    destination_lat     = Column(Float, nullable=False)
    destination_lon     = Column(Float, nullable=False)
    destination_address = Column(String(500), nullable=False)

    # ── Ride type / product ──────────────────────────────────────
    # Provider-specific product ID (e.g. "uberx", "mock_economy")
    ride_type          = Column(String(100), nullable=False)
    # Human-readable label returned by the provider
    ride_type_name     = Column(String(200), nullable=True)
    # Icon/emoji hint for the Flutter UI (optional)
    ride_type_icon     = Column(String(50),  nullable=True)

    # ── Estimates (captured at booking time) ─────────────────────
    estimated_fare_min  = Column(Float, nullable=True)   # lower bound
    estimated_fare_max  = Column(Float, nullable=True)   # upper bound
    estimated_fare      = Column(Float, nullable=True)   # midpoint / single
    currency            = Column(String(10), nullable=False, default="INR")
    estimated_distance_km      = Column(Float, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)

    # ── Actuals (filled after ride completes) ────────────────────
    actual_fare              = Column(Float, nullable=True)
    actual_distance_km       = Column(Float, nullable=True)
    actual_duration_minutes  = Column(Integer, nullable=True)

    # ── Internal status ──────────────────────────────────────────
    # REQUESTED | CONFIRMED | ARRIVING | IN_PROGRESS |
    # COMPLETED | CANCELLED | FAILED
    status = Column(
        String(50),
        nullable=False,
        default="REQUESTED",
        index=True,
    )
    cancellation_reason = Column(String(500), nullable=True)

    # ── Payment ──────────────────────────────────────────────────
    # cash | card | upi | wallet  (may be None if handled by provider)
    payment_method    = Column(String(50),  nullable=True)
    payment_reference = Column(String(255), nullable=True)  # provider txn ref

    # ── Timestamps ───────────────────────────────────────────────
    requested_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at  = Column(DateTime, nullable=True)
    arriving_at   = Column(DateTime, nullable=True)
    started_at    = Column(DateTime, nullable=True)
    completed_at  = Column(DateTime, nullable=True)
    cancelled_at  = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── ORM Relationships ────────────────────────────────────────
    user         = relationship("User",         back_populates="cab_rides")
    provider_ref = relationship("RideProvider", back_populates="cab_rides")
    status_history = relationship(
        "RideStatusHistory",
        back_populates="cab_ride",
        order_by="RideStatusHistory.created_at",
        cascade="all, delete-orphan",
    )

    # ── Composite indexes ────────────────────────────────────────
    __table_args__ = (
        # Fast lookup: all rides for a user, newest first
        Index("ix_cab_rides_user_created", "user_id", "created_at"),
        # Fast lookup by provider + external ride ID
        Index("ix_cab_rides_provider_ext", "provider", "provider_ride_id"),
        # Note: status already indexed via index=True on the column above
    )


class RideStatusHistory(Base):
    """
    Immutable audit log of every status transition for a CabRide.
    One row is inserted each time the ride status changes so we
    have a full timeline for debugging and analytics.
    """
    __tablename__ = "ride_status_history"

    id          = Column(Integer, primary_key=True, index=True)
    cab_ride_id = Column(
        Integer,
        ForeignKey("cab_rides.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Our internal status at this moment
    status          = Column(String(50),  nullable=False)
    # Raw status string from the external provider (may differ)
    provider_status = Column(String(100), nullable=True)
    # Free-text note (e.g. cancellation reason, error message)
    note            = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    cab_ride = relationship("CabRide", back_populates="status_history")