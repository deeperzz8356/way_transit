from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
import auth
import logging

logger = logging.getLogger("way_transit")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    logger.info(f"Authenticating request with token: {token[:10]}...")
    try:
        payload = auth.decode_access_token(token)
        logger.debug(f"Decoded JWT payload: {payload}")
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("JWT payload missing 'sub' claim")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        logger.warning(f"Invalid user_id in token: {user_id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = crud.get_user_by_id(db, user_id)
    if user is None:
        logger.warning(f"User not found for id {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.info(f"Authenticated user id: {user_id}")
    return user.id
