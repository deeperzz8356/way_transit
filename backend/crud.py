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
    return db.query(models.Route).filter(
        models.Route.source == source,
        models.Route.destination == destination
    ).all()

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