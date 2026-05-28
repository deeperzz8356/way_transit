from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

class BookingCreate(BaseModel):
    route_id: int

class BookingResponse(BaseModel):
    id: int
    user_id: int
    route_id: int
    status: str
    created_at: datetime
    route: RouteResponse
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str