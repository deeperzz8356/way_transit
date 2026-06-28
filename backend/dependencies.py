from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
import auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Bypassing auth for now
    user = crud.get_user_by_email(db, email="dummy@example.com")
    if user is None:
        user = crud.create_user(db, email="dummy@example.com", password="dummy")
    return user.id
