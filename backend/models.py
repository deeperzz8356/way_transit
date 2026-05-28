from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    bookings = relationship("Booking", back_populates="user")

class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True)
    source = Column(String, index=True)
    destination = Column(String, index=True)
    transport = Column(String)
    departure_time = Column(String)
    arrival_time = Column(String)
    price = Column(Integer)
    bookings = relationship("Booking", back_populates="route")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True)
    status = Column(String, default="CONFIRMED")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="bookings")
    route = relationship("Route", back_populates="bookings")