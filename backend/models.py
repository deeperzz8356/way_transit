from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, Date
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
    phone = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="user")
    journeys = relationship("Journey", back_populates="user")
    saved_places = relationship("SavedPlace", back_populates="user")
    reward_points = relationship("RewardPoint", back_populates="user")
    wallet = relationship("Wallet", uselist=False, back_populates="user")

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
    route_id = Column(Integer, ForeignKey("routes.id"), index=True)
    from_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    to_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), index=True)
    distance_km = Column(Float)
    image_url = Column(String, nullable=True)
    ticket_code = Column(String, unique=True, index=True)
    source = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    travel_date = Column(Date)
    status = Column(String, default="CONFIRMED")
    booked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    route = relationship("Route", back_populates="bookings")
    departure_stop = relationship("Stop", foreign_keys=[from_stop_id], back_populates="departure_bookings")
    arrival_stop = relationship("Stop", foreign_keys=[to_stop_id], back_populates="arrival_bookings")
    trip = relationship("Trip", back_populates="bookings")
    reward_points = relationship("RewardPoint", back_populates="booking")


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
    raw_text = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Journey(Base):
    __tablename__ = "journeys"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    from_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    to_stop_id = Column(Integer, ForeignKey("stops.id"), index=True)
    total_fare = Column(Float)
    total_duration = Column(Integer)
    total_distance = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="journeys")
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

class Concession(Base):
    __tablename__ = "concessions"
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), index=True)
    type = Column(String)
    discount_pct = Column(Float)
    requires_id = Column(Boolean, default=False)

    operator = relationship("Operator", back_populates="concessions")