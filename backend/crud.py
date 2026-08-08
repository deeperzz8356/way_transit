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
    ticket_trip_id: int = None,
):
    """Create a wallet ticket with actual ticket identity fields."""
    mode_n = normalize_mode(mode) if mode else infer_mode_from_operator(operator_name)

    if ticket_trip_id is not None:
        trip = (
            db.query(models.TicketTrip)
            .filter(
                models.TicketTrip.id == ticket_trip_id,
                models.TicketTrip.user_id == user_id,
            )
            .first()
        )
        if not trip:
            raise ValueError("Trip not found")

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
        ticket_trip_id=ticket_trip_id,
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
    booking.status = "USED"
    booking.journey_started_at = booking.journey_started_at
    booking.journey_estimated_end_at = booking.journey_estimated_end_at
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
    return booking, None


def get_user_wallet(db: Session, user_id: int, mode: Optional[str] = None):
    """Return (ungrouped_tickets, trips, passes).

    Ungrouped tickets are bookings with ticket_trip_id IS NULL.
    When mode is set, ungrouped tickets are mode-filtered; trip rows are
    still returned (callers filter nested tickets when serializing).
    """
    today = date.today()
    all_user_tickets = (
        db.query(models.Booking)
        .filter(models.Booking.user_id == user_id)
        .order_by(models.Booking.booked_at.desc())
        .all()
    )
    for t in all_user_tickets:
        if (
            t.travel_date
            and t.travel_date < today
            and t.status in ("CONFIRMED", "IN_PROGRESS")
        ):
            t.status = "EXPIRED"
            db.add(t)
    db.commit()

    mode_n = normalize_mode(mode) if mode and mode != "all" else None

    def _mode_ok(t):
        return mode_n is None or t.mode == mode_n

    ungrouped = [
        t for t in all_user_tickets if t.ticket_trip_id is None and _mode_ok(t)
    ]

    trips = (
        db.query(models.TicketTrip)
        .filter(models.TicketTrip.user_id == user_id)
        .order_by(models.TicketTrip.updated_at.desc())
        .all()
    )

    passes = (
        db.query(models.UserPass)
        .filter(models.UserPass.user_id == user_id)
        .order_by(models.UserPass.created_at.desc())
        .all()
    )
    return ungrouped, trips, passes


def create_ticket_trip(
    db: Session,
    user_id: int,
    name: str,
    notes: Optional[str] = None,
    travel_date: Optional[str] = None,
):
    cleaned = (name or "").strip()
    if not cleaned:
        raise ValueError("Trip name is required")
    trip = models.TicketTrip(
        user_id=user_id,
        name=cleaned,
        notes=(notes or "").strip() or None,
        travel_date=_parse_travel_date(travel_date) if isinstance(travel_date, str) else travel_date,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def list_user_ticket_trips(db: Session, user_id: int):
    return (
        db.query(models.TicketTrip)
        .filter(models.TicketTrip.user_id == user_id)
        .order_by(models.TicketTrip.updated_at.desc())
        .all()
    )


def get_ticket_trip(db: Session, user_id: int, trip_id: int):
    return (
        db.query(models.TicketTrip)
        .filter(
            models.TicketTrip.id == trip_id,
            models.TicketTrip.user_id == user_id,
        )
        .first()
    )


def update_ticket_trip(
    db: Session,
    user_id: int,
    trip_id: int,
    name: Optional[str] = None,
    notes: Optional[str] = None,
    travel_date: Optional[str] = None,
):
    trip = get_ticket_trip(db, user_id, trip_id)
    if not trip:
        return None, "Trip not found"
    if name is not None:
        cleaned = name.strip()
        if not cleaned:
            return None, "Trip name is required"
        trip.name = cleaned
    if notes is not None:
        trip.notes = notes.strip() or None
    if travel_date is not None:
        if travel_date == "":
            trip.travel_date = None
        else:
            trip.travel_date = (
                _parse_travel_date(travel_date)
                if isinstance(travel_date, str)
                else travel_date
            )
    trip.updated_at = datetime.utcnow()
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip, None


def delete_ticket_trip(db: Session, user_id: int, trip_id: int):
    trip = (
        db.query(models.TicketTrip)
        .filter(
            models.TicketTrip.id == trip_id,
            models.TicketTrip.user_id == user_id,
        )
        .first()
    )
    if not trip:
        return False, "Trip not found"
    members = (
        db.query(models.Booking)
        .filter(
            models.Booking.ticket_trip_id == trip_id,
            models.Booking.user_id == user_id,
        )
        .all()
    )
    for booking in members:
        booking.ticket_trip_id = None
        db.add(booking)
    db.delete(trip)
    db.commit()
    return True, None


def add_tickets_to_trip(
    db: Session,
    user_id: int,
    trip_id: int,
    ticket_ids: list[int],
):
    trip = get_ticket_trip(db, user_id, trip_id)
    if not trip:
        return None, "Trip not found"
    if not ticket_ids:
        return trip, None

    bookings = (
        db.query(models.Booking)
        .filter(
            models.Booking.user_id == user_id,
            models.Booking.id.in_(ticket_ids),
        )
        .all()
    )
    found_ids = {b.id for b in bookings}
    missing = [tid for tid in ticket_ids if tid not in found_ids]
    if missing:
        return None, f"Tickets not found: {missing}"

    for booking in bookings:
        booking.ticket_trip_id = trip_id
        db.add(booking)
    trip.updated_at = datetime.utcnow()
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip, None


def remove_ticket_from_trip(
    db: Session,
    user_id: int,
    trip_id: int,
    ticket_id: int,
):
    trip = (
        db.query(models.TicketTrip)
        .filter(
            models.TicketTrip.id == trip_id,
            models.TicketTrip.user_id == user_id,
        )
        .first()
    )
    if not trip:
        return None, "Trip not found"
    booking = (
        db.query(models.Booking)
        .filter(
            models.Booking.id == ticket_id,
            models.Booking.user_id == user_id,
            models.Booking.ticket_trip_id == trip_id,
        )
        .first()
    )
    if not booking:
        return None, "Ticket not found in this trip"
    booking.ticket_trip_id = None
    db.add(booking)
    trip.updated_at = datetime.utcnow()
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip, None


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