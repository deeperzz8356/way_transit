from datetime import datetime
from sqlalchemy.orm import Session
import models
import auth

def create_user(
    db: Session,
    email: str,
    password: str,
    phone: str | None = None,
    name: str | None = None,
    google_id: str | None = None,
    profile_image: str | None = None,
    auth_provider: str | None = None,
    is_verified: bool = False,
):
    hashed_password = auth.hash_password(password) if password else None
    user = models.User(
        email=email,
        password=hashed_password,
        phone=phone,
        name=name,
        google_id=google_id,
        profile_image=profile_image,
        auth_provider=auth_provider,
        is_verified=is_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str):
    if not email:
        return None
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_phone(db: Session, phone: str):
    if not phone:
        return None
    return db.query(models.User).filter(models.User.phone == phone).first()


def get_user_by_google_id(db: Session, google_id: str):
    if not google_id:
        return None
    return db.query(models.User).filter(models.User.google_id == google_id).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def update_user(db: Session, user: models.User, **fields):
    for key, value in fields.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: models.User):
    # Remove related user-owned records first to avoid foreign key issues
    db.query(models.Booking).filter(models.Booking.user_id == user.id).delete(synchronize_session=False)
    db.query(models.Journey).filter(models.Journey.user_id == user.id).delete(synchronize_session=False)
    db.query(models.SavedPlace).filter(models.SavedPlace.user_id == user.id).delete(synchronize_session=False)
    db.query(models.RewardPoint).filter(models.RewardPoint.user_id == user.id).delete(synchronize_session=False)
    db.query(models.Wallet).filter(models.Wallet.user_id == user.id).delete(synchronize_session=False)
    db.query(models.TicketIngestJob).filter(models.TicketIngestJob.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()


def get_otp_by_phone(db: Session, phone: str):
    return db.query(models.OTPCode).filter(models.OTPCode.phone == phone).first()


def create_or_update_otp_code(db: Session, phone: str, hashed_code: str, expires_at: datetime, now: datetime):
    otp_record = get_otp_by_phone(db, phone)
    if otp_record:
        otp_record.hashed_code = hashed_code
        otp_record.expires_at = expires_at
        otp_record.last_sent_at = now
        otp_record.request_count = (otp_record.request_count or 0) + 1
        db.add(otp_record)
    else:
        otp_record = models.OTPCode(
            phone=phone,
            hashed_code=hashed_code,
            expires_at=expires_at,
            created_at=now,
            last_sent_at=now,
            first_requested_at=now,
            request_count=1,
        )
        db.add(otp_record)
    db.commit()
    db.refresh(otp_record)
    return otp_record


def increment_otp_failed_attempts(db: Session, otp_record: models.OTPCode):
    otp_record.failed_attempts = (otp_record.failed_attempts or 0) + 1
    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)
    return otp_record


def delete_otp_code(db: Session, otp_record: models.OTPCode):
    db.delete(otp_record)
    db.commit()

def get_routes(db: Session, source: str, destination: str):
    from sqlalchemy import text
    query = text("""
        SELECT DISTINCT r.id
        FROM routes r
        JOIN trips t ON t.route_id = r.id
        JOIN stop_times st_start ON st_start.trip_id = t.id
        JOIN stops s_start ON st_start.stop_id = s_start.id
        JOIN stop_times st_end ON st_end.trip_id = t.id
        JOIN stops s_end ON st_end.stop_id = s_end.id
        WHERE st_start.stop_sequence < st_end.stop_sequence
          AND (lower(s_start.name) LIKE lower(:source) OR lower(s_start.stop_code) = lower(:source))
          AND (lower(s_end.name) LIKE lower(:destination) OR lower(s_end.stop_code) = lower(:destination))
    """)
    route_ids = [row[0] for row in db.execute(query, {
        "source": f"%{source}%",
        "destination": f"%{destination}%"
    }).all()]
    return db.query(models.Route).filter(models.Route.id.in_(route_ids)).all()

def create_booking(db: Session, user_id: int, route_id: int):
    booking = models.Booking(
        user_id=user_id,
        route_id=route_id,
        status="CONFIRMED"
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

import uuid
from datetime import datetime, timedelta, date
from typing import Optional

from platform_colors import normalize_mode, infer_mode_from_operator


def find_duplicate_ticket(
    db: Session,
    user_id: int,
    ticket_number: Optional[str],
    mode: Optional[str],
):
    if not ticket_number or not ticket_number.strip():
        return None
    mode_n = normalize_mode(mode)
    return (
        db.query(models.Booking)
        .filter(
            models.Booking.user_id == user_id,
            models.Booking.ticket_number == ticket_number.strip(),
            models.Booking.mode == mode_n,
        )
        .first()
    )


def _parse_travel_date(value: Optional[str]):
    if not value:
        return None
    raw = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            continue
    return None


def create_unified_ticket(
    db: Session,
    user_id: int,
    source: str,
    destination: str,
    image_url: str = None,
    ticket_number: str = None,
    qr_payload: str = None,
    mode: str = None,
    operator_name: str = None,
    travel_date: str = None,
    class_name: str = None,
    fare: float = None,
    source_type: str = "manual",
    operator_id: int = None,
):
    """Create a wallet ticket with actual ticket identity fields."""
    mode_n = normalize_mode(mode) if mode else infer_mode_from_operator(operator_name)

    ticket_code = str(uuid.uuid4())
    booking = models.Booking(
        user_id=user_id,
        route_id=None,
        status="CONFIRMED",
        ticket_code=ticket_code,
        ticket_number=(ticket_number or "").strip() or None,
        qr_payload=(qr_payload or "").strip() or None,
        mode=mode_n,
        operator_id=operator_id,
        operator_name=operator_name,
        class_name=class_name,
        fare=fare,
        source_type=source_type or "manual",
        image_url=image_url,
        source=source,
        destination=destination,
        travel_date=_parse_travel_date(travel_date) if isinstance(travel_date, str) else travel_date,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def find_stop_by_name(db: Session, name: str):
    if not name:
        return None
    return (
        db.query(models.Stop)
        .filter(models.Stop.name.ilike(f"%{name.strip()}%"))
        .first()
    )


def _parse_datetime(value: Optional[str]):
    if not value:
        return None
    raw = value.strip()
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw[:19], fmt)
        except ValueError:
            continue
    return None


def deactivate_other_active_tickets(db: Session, user_id: int, keep_booking_id: int):
    """Only one ticket can be the auto-active journey at a time."""
    others = (
        db.query(models.Booking)
        .filter(
            models.Booking.user_id == user_id,
            models.Booking.status == "IN_PROGRESS",
            models.Booking.id != keep_booking_id,
        )
        .all()
    )
    for other in others:
        other.status = "CONFIRMED"
        other.journey_started_at = None
        other.journey_estimated_end_at = None
        db.add(other)
        for j in (
            db.query(models.Journey)
            .filter(
                models.Journey.booking_id == other.id,
                models.Journey.status == "active",
            )
            .all()
        ):
            j.status = "superseded"
            db.add(j)


def start_journey_for_ticket(
    db: Session,
    user_id: int,
    booking_id: int,
    start_time: Optional[str] = None,
    estimated_end_time: Optional[str] = None,
    make_active: bool = True,
):
    booking = (
        db.query(models.Booking)
        .filter(models.Booking.id == booking_id, models.Booking.user_id == user_id)
        .first()
    )
    if not booking:
        return None, "Ticket not found"
    if booking.status == "USED":
        return None, "Ticket already used"
    if booking.status == "EXPIRED":
        return None, "Ticket expired"

    started = _parse_datetime(start_time) or datetime.utcnow()
    estimated_end = _parse_datetime(estimated_end_time)
    if estimated_end and estimated_end <= started:
        return None, "Estimated end time must be after start time"

    if make_active:
        deactivate_other_active_tickets(db, user_id, booking.id)

    from_stop = find_stop_by_name(db, booking.source)
    to_stop = find_stop_by_name(db, booking.destination)
    duration_min = None
    if estimated_end:
        duration_min = int((estimated_end - started).total_seconds() // 60)

    journey = models.Journey(
        user_id=user_id,
        booking_id=booking.id,
        from_stop_id=from_stop.id if from_stop else None,
        to_stop_id=to_stop.id if to_stop else None,
        total_fare=booking.fare,
        total_duration=duration_min,
        status="active",
        started_at=started,
        estimated_end_at=estimated_end,
    )
    booking.status = "IN_PROGRESS"
    booking.journey_started_at = started
    booking.journey_estimated_end_at = estimated_end
    db.add(journey)
    db.add(booking)
    db.commit()
    db.refresh(journey)
    db.refresh(booking)
    
    # ✅ AUTO-CREATE UserTrip when ticket is activated
    # This makes the trip visible in My Trips and contributes to My Stats
    try:
        user_trip = models.UserTrip(
            user_id=user_id,
            status="in_progress",
            transport_mode=booking.mode or "transit",
            origin=booking.source or "Unknown",
            destination=booking.destination or "Unknown",
            started_at=started,
            completed_at=estimated_end,
            distance_km=0,  # Will be calculated if available
            duration_minutes=duration_min,
            fare_amount=booking.fare or 0,
            booking_id=booking.id,  # Link back to original booking/ticket
        )
        db.add(user_trip)
        db.commit()
        db.refresh(user_trip)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Auto-created UserTrip id={user_trip.id} for booking_id={booking.id}")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ Failed to auto-create UserTrip: {e}")
        # Don't fail the whole operation if UserTrip creation fails
    
    return journey, None


def delete_ticket(db: Session, user_id: int, booking_id: int):
    booking = (
        db.query(models.Booking)
        .filter(models.Booking.id == booking_id, models.Booking.user_id == user_id)
        .first()
    )
    if not booking:
        return False, "Ticket not found"
    # Clear ingest job links
    jobs = (
        db.query(models.TicketIngestJob)
        .filter(models.TicketIngestJob.booking_id == booking.id)
        .all()
    )
    for job in jobs:
        job.booking_id = None
        db.add(job)
    # Remove related journeys
    for j in (
        db.query(models.Journey).filter(models.Journey.booking_id == booking.id).all()
    ):
        db.delete(j)
    # Remove reward points tied to booking if any
    for rp in (
        db.query(models.RewardPoint)
        .filter(models.RewardPoint.booking_id == booking.id)
        .all()
    ):
        db.delete(rp)
    db.delete(booking)
    db.commit()
    return True, None


def complete_ticket_journey(db: Session, user_id: int, booking_id: int):
    booking = (
        db.query(models.Booking)
        .filter(models.Booking.id == booking_id, models.Booking.user_id == user_id)
        .first()
    )
    if not booking:
        return None, "Ticket not found"

    now = datetime.utcnow()
    booking.status = "USED"
    active = (
        db.query(models.Journey)
        .filter(
            models.Journey.booking_id == booking.id,
            models.Journey.status == "active",
        )
        .all()
    )
    for j in active:
        j.status = "completed"
        db.add(j)
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # --- Auto-create a UserTrip from this completed booking ---
    _auto_create_trip_from_booking(db, booking, now)

    return booking, None


def _auto_create_trip_from_booking(db: Session, booking: models.Booking, completed_at: datetime):
    """Create a UserTrip record from a completed Booking, if not already exists."""
    # Avoid duplicates
    existing = (
        db.query(models.UserTrip)
        .filter(models.UserTrip.booking_id == booking.id)
        .first()
    )
    if existing:
        return existing

    started_at = booking.journey_started_at or booking.booked_at or completed_at
    distance = booking.distance_km or 0.0
    fare = booking.fare or 0.0
    # Estimate duration from journey times if available
    duration_min = 0
    if booking.journey_started_at and booking.journey_estimated_end_at:
        duration_min = int(
            (booking.journey_estimated_end_at - booking.journey_started_at).total_seconds() // 60
        )

    user_trip = models.UserTrip(
        user_id=booking.user_id,
        booking_id=booking.id,
        origin=booking.source or "Unknown",
        destination=booking.destination or "Unknown",
        transport_mode=booking.mode or "other",
        total_distance_km=distance,
        total_duration_minutes=duration_min,
        total_fare=fare,
        currency="INR",
        started_at=started_at,
        completed_at=completed_at,
        route_name=None,
        operator_name=booking.operator_name,
        ticket_reference=booking.ticket_number or booking.ticket_code,
        num_transfers=0,
        status="completed",
    )
    db.add(user_trip)
    db.commit()
    db.refresh(user_trip)

    # Create a single leg matching the booking
    leg = models.UserTripLeg(
        trip_id=user_trip.id,
        sequence=1,
        transport_mode=booking.mode or "other",
        origin=booking.source or "Unknown",
        destination=booking.destination or "Unknown",
        distance_km=distance,
        duration_minutes=duration_min,
        fare=fare,
        started_at=started_at,
        completed_at=completed_at,
        operator_name=booking.operator_name,
        ticket_reference=booking.ticket_number or booking.ticket_code,
    )
    db.add(leg)
    db.commit()
    return user_trip



def get_user_wallet(db: Session, user_id: int, mode: Optional[str] = None):
    q = db.query(models.Booking).filter(models.Booking.user_id == user_id)
    if mode and mode != "all":
        q = q.filter(models.Booking.mode == normalize_mode(mode))
    tickets = q.order_by(models.Booking.booked_at.desc()).all()
    # Expire dated tickets
    today = date.today()
    for t in tickets:
        if (
            t.travel_date
            and t.travel_date < today
            and t.status in ("CONFIRMED", "IN_PROGRESS")
        ):
            t.status = "EXPIRED"
            db.add(t)
    db.commit()

    passes = (
        db.query(models.UserPass)
        .filter(models.UserPass.user_id == user_id)
        .order_by(models.UserPass.created_at.desc())
        .all()
    )
    return tickets, passes


def ensure_demo_pass_products(db: Session):
    """Seed a couple of pass products if none exist."""
    if db.query(models.Pass).count() > 0:
        return
    op = db.query(models.Operator).first()
    op_id = op.id if op else None
    for name, days, price, mode in [
        ("Daily Suburban Pass", 1, 50.0, "rail"),
        ("Metro Day Pass", 1, 80.0, "metro"),
        ("BEST Day Pass", 1, 40.0, "bus"),
    ]:
        db.add(
            models.Pass(
                operator_id=op_id,
                name=name,
                validity_days=days,
                price=price,
                mode_coverage=mode,
                is_active=True,
            )
        )
    db.commit()


def add_user_pass(db: Session, user_id: int, pass_id: int):
    product = db.query(models.Pass).filter(models.Pass.id == pass_id).first()
    if not product:
        return None
    valid_until = datetime.utcnow() + timedelta(days=product.validity_days or 1)
    up = models.UserPass(
        user_id=user_id,
        pass_id=pass_id,
        valid_until=valid_until,
        status="active",
    )
    db.add(up)
    db.commit()
    db.refresh(up)
    return up

def create_route(db: Session, source: str, destination: str, transport: str, departure_time: str, arrival_time: str, price: int):
    route = models.Route(
        name=f"{source} to {destination}",
        mode=transport
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return route


def create_ticket_ingest_job(db: Session, user_id: int, image_url: str):
    job = models.TicketIngestJob(
        user_id=user_id,
        image_url=image_url,
        status="uploaded",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_ticket_ingest_job(db: Session, job_id: int, user_id: int = None):
    q = db.query(models.TicketIngestJob).filter(models.TicketIngestJob.id == job_id)
    if user_id is not None:
        q = q.filter(models.TicketIngestJob.user_id == user_id)
    return q.first()


def update_ticket_ingest_job(db: Session, job: models.TicketIngestJob, **fields):
    for key, value in fields.items():
        if hasattr(job, key):
            setattr(job, key, value)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


# ─────────────────────────────────────────────
#  UserTrip CRUD
# ─────────────────────────────────────────────

def get_user_trips(
    db: Session,
    user_id: int,
    status: Optional[str] = None,
    transport_mode: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Return user's trips, newest first, with optional filters."""
    q = (
        db.query(models.UserTrip)
        .filter(models.UserTrip.user_id == user_id)
    )
    if status and status != "all":
        q = q.filter(models.UserTrip.status == status)
    if transport_mode and transport_mode != "all":
        q = q.filter(models.UserTrip.transport_mode == transport_mode)
    if date_from:
        q = q.filter(models.UserTrip.started_at >= date_from)
    if date_to:
        q = q.filter(models.UserTrip.started_at <= date_to)
    return q.order_by(models.UserTrip.started_at.desc().nullslast()).offset(offset).limit(limit).all()


def get_user_trip_by_id(db: Session, trip_id: int, user_id: int):
    return (
        db.query(models.UserTrip)
        .filter(models.UserTrip.id == trip_id, models.UserTrip.user_id == user_id)
        .first()
    )


def create_user_trip(db: Session, user_id: int, data) -> models.UserTrip:
    """Manually create a UserTrip (e.g. for walking / manual journeys)."""
    trip = models.UserTrip(
        user_id=user_id,
        booking_id=None,
        origin=data.origin,
        destination=data.destination,
        origin_lat=data.origin_lat,
        origin_lon=data.origin_lon,
        destination_lat=data.destination_lat,
        destination_lon=data.destination_lon,
        transport_mode=data.transport_mode or "other",
        total_distance_km=data.total_distance_km or 0.0,
        total_duration_minutes=data.total_duration_minutes or 0,
        total_fare=data.total_fare or 0.0,
        currency=data.currency or "INR",
        started_at=data.started_at,
        completed_at=data.completed_at or datetime.utcnow(),
        route_name=data.route_name,
        operator_name=data.operator_name,
        ticket_reference=data.ticket_reference,
        num_transfers=data.num_transfers or 0,
        status=data.status or "completed",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Create legs if provided
    legs_data = data.legs or []
    if not legs_data:
        # Single auto leg from trip fields
        leg = models.UserTripLeg(
            trip_id=trip.id,
            sequence=1,
            transport_mode=trip.transport_mode or "other",
            origin=trip.origin,
            destination=trip.destination,
            distance_km=trip.total_distance_km,
            duration_minutes=trip.total_duration_minutes,
            fare=trip.total_fare,
            started_at=trip.started_at,
            completed_at=trip.completed_at,
        )
        db.add(leg)
    else:
        for leg_data in legs_data:
            leg = models.UserTripLeg(
                trip_id=trip.id,
                sequence=leg_data.sequence,
                transport_mode=leg_data.transport_mode,
                origin=leg_data.origin,
                destination=leg_data.destination,
                origin_lat=leg_data.origin_lat,
                origin_lon=leg_data.origin_lon,
                destination_lat=leg_data.destination_lat,
                destination_lon=leg_data.destination_lon,
                distance_km=leg_data.distance_km,
                duration_minutes=leg_data.duration_minutes,
                fare=leg_data.fare,
                started_at=leg_data.started_at,
                completed_at=leg_data.completed_at,
                route_name=leg_data.route_name,
                operator_name=leg_data.operator_name,
                ticket_reference=leg_data.ticket_reference,
            )
            db.add(leg)
    db.commit()
    db.refresh(trip)
    return trip


def update_user_trip(db: Session, trip: models.UserTrip, data) -> models.UserTrip:
    update_fields = data.model_dump(exclude_unset=True)
    for key, value in update_fields.items():
        if hasattr(trip, key) and value is not None:
            setattr(trip, key, value)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def delete_user_trip(db: Session, trip: models.UserTrip):
    db.delete(trip)
    db.commit()


# ─────────────────────────────────────────────
#  Travel Statistics
# ─────────────────────────────────────────────

# CO2 emission factors in kg per km — centralized and configurable
_CO2_KG_PER_KM = {
    "walking": 0.0,
    "bike": 0.0,
    "car": 0.171,      # average petrol car (UK DEFRA baseline)
    "cab": 0.171,
    "bus": 0.089,
    "train": 0.041,
    "rail": 0.041,
    "metro": 0.033,
    "auto": 0.100,
    "other": 0.100,
}
_CAR_BASELINE_KG_PER_KM = 0.171   # kg CO₂/km for comparison


def _get_trips_in_period(db: Session, user_id: int, period: str):
    """Return completed trips filtered by period string."""
    from datetime import date, timedelta
    now = datetime.utcnow()
    q = (
        db.query(models.UserTrip)
        .filter(
            models.UserTrip.user_id == user_id,
            models.UserTrip.status == "completed",
        )
    )
    if period == "this_week":
        monday = now - timedelta(days=now.weekday())
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        q = q.filter(models.UserTrip.started_at >= monday)
    elif period == "this_month":
        first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        q = q.filter(models.UserTrip.started_at >= first)
    elif period == "last_3_months":
        cutoff = now - timedelta(days=91)
        q = q.filter(models.UserTrip.started_at >= cutoff)
    elif period == "this_year":
        first = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        q = q.filter(models.UserTrip.started_at >= first)
    # "all_time" — no filter
    return q.all()


def compute_travel_stats(db: Session, user_id: int, period: str = "all_time"):
    """Compute all travel statistics for a user within a given period."""
    from collections import defaultdict
    from datetime import timedelta

    trips = _get_trips_in_period(db, user_id, period)

    total_trips = len(trips)
    total_distance = sum(t.total_distance_km or 0.0 for t in trips)
    total_duration = sum(t.total_duration_minutes or 0 for t in trips)
    total_fare = sum(t.total_fare or 0.0 for t in trips)

    avg_distance = (total_distance / total_trips) if total_trips else 0.0
    avg_duration = (total_duration / total_trips) if total_trips else 0.0

    # By mode
    mode_map: dict = defaultdict(lambda: {"trip_count": 0, "total_distance_km": 0.0, "total_duration_minutes": 0, "total_fare": 0.0})
    for t in trips:
        m = t.transport_mode or "other"
        mode_map[m]["trip_count"] += 1
        mode_map[m]["total_distance_km"] += t.total_distance_km or 0.0
        mode_map[m]["total_duration_minutes"] += t.total_duration_minutes or 0
        mode_map[m]["total_fare"] += t.total_fare or 0.0

    by_mode = [
        {
            "transport_mode": mode,
            "trip_count": v["trip_count"],
            "total_distance_km": round(v["total_distance_km"], 2),
            "total_duration_minutes": v["total_duration_minutes"],
            "total_fare": round(v["total_fare"], 2),
        }
        for mode, v in sorted(mode_map.items(), key=lambda x: -x[1]["trip_count"])
    ]
    most_used_mode = by_mode[0]["transport_mode"] if by_mode else None

    # Weekly stats (last 12 weeks)
    weekly_map: dict = defaultdict(lambda: {"trip_count": 0, "total_distance_km": 0.0, "total_fare": 0.0})
    for t in trips:
        if t.started_at:
            monday = t.started_at - timedelta(days=t.started_at.weekday())
            week_key = monday.strftime("%Y-%m-%d")
            weekly_map[week_key]["trip_count"] += 1
            weekly_map[week_key]["total_distance_km"] += t.total_distance_km or 0.0
            weekly_map[week_key]["total_fare"] += t.total_fare or 0.0
    weekly = [
        {
            "week_start": k,
            "trip_count": v["trip_count"],
            "total_distance_km": round(v["total_distance_km"], 2),
            "total_fare": round(v["total_fare"], 2),
        }
        for k, v in sorted(weekly_map.items())
    ]

    # Monthly stats
    monthly_map: dict = defaultdict(lambda: {"trip_count": 0, "total_distance_km": 0.0, "total_fare": 0.0})
    for t in trips:
        if t.started_at:
            month_key = t.started_at.strftime("%Y-%m")
            monthly_map[month_key]["trip_count"] += 1
            monthly_map[month_key]["total_distance_km"] += t.total_distance_km or 0.0
            monthly_map[month_key]["total_fare"] += t.total_fare or 0.0
    monthly = [
        {
            "month": k,
            "trip_count": v["trip_count"],
            "total_distance_km": round(v["total_distance_km"], 2),
            "total_fare": round(v["total_fare"], 2),
        }
        for k, v in sorted(monthly_map.items())
    ]

    # Green travel
    total_co2 = 0.0
    public_distance = 0.0
    walking_distance = 0.0
    for t in trips:
        mode = (t.transport_mode or "other").lower()
        dist = t.total_distance_km or 0.0
        factor = _CO2_KG_PER_KM.get(mode, _CO2_KG_PER_KM["other"])
        total_co2 += dist * factor
        if mode in ("bus", "train", "rail", "metro"):
            public_distance += dist
        if mode == "walking":
            walking_distance += dist
    co2_saved = max(0.0, total_distance * _CAR_BASELINE_KG_PER_KM - total_co2)

    # Greenest mode used (lowest non-zero emission factor that user actually used)
    used_modes = list(mode_map.keys())
    greenest = None
    if used_modes:
        greenest = min(used_modes, key=lambda m: _CO2_KG_PER_KM.get(m, 999))

    return {
        "total_trips": total_trips,
        "total_distance_km": round(total_distance, 2),
        "total_duration_minutes": total_duration,
        "total_fare": round(total_fare, 2),
        "average_distance_km": round(avg_distance, 2),
        "average_duration_minutes": round(avg_duration, 1),
        "most_used_mode": most_used_mode,
        "by_mode": by_mode,
        "weekly": weekly,
        "monthly": monthly,
        "green": {
            "total_co2_kg": round(total_co2, 3),
            "co2_saved_vs_car_kg": round(co2_saved, 3),
            "public_transport_distance_km": round(public_distance, 2),
            "walking_distance_km": round(walking_distance, 2),
            "greenest_mode": greenest,
            "note": "Estimated values based on standard DEFRA/IEA emission factors",
        },
        "period": period,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Ride-Booking CRUD  (cab / on-demand rides)
# ─────────────────────────────────────────────────────────────────────────────

def get_active_provider(db: Session, name: str = "mock") -> models.RideProvider:
    """Return the RideProvider row for the given slug. Raises ValueError if missing."""
    provider = (
        db.query(models.RideProvider)
        .filter(models.RideProvider.name == name, models.RideProvider.is_active == True)
        .first()
    )
    if not provider:
        raise ValueError(f"Provider '{name}' not found or inactive.")
    return provider


def create_cab_ride(
    db: Session,
    user_id: int,
    provider_id: int,
    provider: str,
    provider_ride_id: str,
    provider_status: str,
    pickup_lat: float,
    pickup_lon: float,
    pickup_address: str,
    destination_lat: float,
    destination_lon: float,
    destination_address: str,
    ride_type: str,
    ride_type_name: str,
    ride_type_icon: str,
    estimated_fare_min: float,
    estimated_fare_max: float,
    estimated_fare: float,
    estimated_distance_km: float,
    estimated_duration_minutes: int,
    payment_method: str,
    status: str = "CONFIRMED",
    currency: str = "INR",
) -> models.CabRide:
    """Insert a new CabRide row and seed its first status history entry."""
    ride = models.CabRide(
        user_id=user_id,
        provider_id=provider_id,
        provider=provider,
        provider_ride_id=provider_ride_id,
        provider_status=provider_status,
        pickup_lat=pickup_lat,
        pickup_lon=pickup_lon,
        pickup_address=pickup_address,
        destination_lat=destination_lat,
        destination_lon=destination_lon,
        destination_address=destination_address,
        ride_type=ride_type,
        ride_type_name=ride_type_name,
        ride_type_icon=ride_type_icon,
        estimated_fare_min=estimated_fare_min,
        estimated_fare_max=estimated_fare_max,
        estimated_fare=estimated_fare,
        estimated_distance_km=estimated_distance_km,
        estimated_duration_minutes=estimated_duration_minutes,
        payment_method=payment_method,
        currency=currency,
        status=status,
        confirmed_at=datetime.utcnow() if status == "CONFIRMED" else None,
    )
    db.add(ride)
    db.flush()   # get the id without full commit

    # Seed the first status history row
    _add_status_history(
        db,
        cab_ride_id=ride.id,
        status=status,
        provider_status=provider_status,
        note="Ride created and confirmed by provider.",
    )
    db.commit()
    db.refresh(ride)
    return ride


def get_cab_ride(db: Session, ride_id: int, user_id: int) -> models.CabRide | None:
    """Return a single CabRide owned by user_id, or None."""
    return (
        db.query(models.CabRide)
        .filter(models.CabRide.id == ride_id, models.CabRide.user_id == user_id)
        .first()
    )


def get_user_cab_rides(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
) -> list[models.CabRide]:
    """Return the authenticated user's cab ride history, newest first."""
    q = db.query(models.CabRide).filter(models.CabRide.user_id == user_id)
    if status:
        q = q.filter(models.CabRide.status == status.upper())
    return q.order_by(models.CabRide.created_at.desc()).offset(offset).limit(limit).all()


def update_cab_ride_status(
    db: Session,
    ride: models.CabRide,
    new_status: str,
    provider_status: str | None = None,
    note: str | None = None,
    cancellation_reason: str | None = None,
    actual_fare: float | None = None,
    actual_distance_km: float | None = None,
    actual_duration_minutes: int | None = None,
) -> models.CabRide:
    """
    Update ride status and fill the corresponding timestamp column.
    Always appends a RideStatusHistory row.
    """
    now = datetime.utcnow()
    ride.status = new_status

    if provider_status:
        ride.provider_status = provider_status

    # Fill the appropriate timestamp for this status
    _ts_map = {
        "CONFIRMED":    "confirmed_at",
        "ARRIVING":     "arriving_at",
        "IN_PROGRESS":  "started_at",
        "COMPLETED":    "completed_at",
        "CANCELLED":    "cancelled_at",
    }
    ts_col = _ts_map.get(new_status)
    if ts_col and getattr(ride, ts_col) is None:
        setattr(ride, ts_col, now)

    if cancellation_reason:
        ride.cancellation_reason = cancellation_reason
    if actual_fare is not None:
        ride.actual_fare = actual_fare
    if actual_distance_km is not None:
        ride.actual_distance_km = actual_distance_km
    if actual_duration_minutes is not None:
        ride.actual_duration_minutes = actual_duration_minutes

    _add_status_history(
        db,
        cab_ride_id=ride.id,
        status=new_status,
        provider_status=provider_status,
        note=note,
    )
    db.commit()
    db.refresh(ride)
    return ride


def _add_status_history(
    db: Session,
    cab_ride_id: int,
    status: str,
    provider_status: str | None = None,
    note: str | None = None,
) -> models.RideStatusHistory:
    """Internal helper — always called within an open transaction."""
    entry = models.RideStatusHistory(
        cab_ride_id=cab_ride_id,
        status=status,
        provider_status=provider_status,
        note=note,
    )
    db.add(entry)
    return entry

