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

def create_booking_order(db: Session, user_id: int, route_id: int, source: str, destination: str, distance_km: float, fare: float, payment_order_id: str):
    booking = models.Booking(
        user_id=user_id,
        route_id=route_id,
        status="PENDING",
        payment_status="pending",
        payment_order_id=payment_order_id,
        fare=fare,
        source=source,
        destination=destination,
        distance_km=distance_km
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

def create_route(db: Session, source: str, destination: str, transport: str, departure_time: str, arrival_time: str, price: int):
    route = models.Route(
        source=source,
        destination=destination,
        transport=transport,
        departure_time=departure_time,
        arrival_time=arrival_time,
        price=price
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return route