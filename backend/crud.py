from sqlalchemy.orm import Session
import models
import auth

def create_user(db: Session, email: str, password: str):
    hashed_password = auth.hash_password(password)
    user = models.User(email=email, password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

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

def create_unified_ticket(db: Session, user_id: int, source: str, destination: str, image_url: str = None):
    """Create a wallet ticket linked to a lightweight route so source/destination persist."""
    route = models.Route(
        name=f"{source} to {destination}",
        mode="transit",
        is_active=True,
    )
    db.add(route)
    db.flush()

    ticket_code = str(uuid.uuid4())
    booking = models.Booking(
        user_id=user_id,
        route_id=route.id,
        status="CONFIRMED",
        ticket_code=ticket_code,
        image_url=image_url,
        source=source,
        destination=destination,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

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