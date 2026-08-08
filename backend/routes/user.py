from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from database import SessionLocal
import crud
import schemas
import auth
from dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["user"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    existing_user = crud.get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return crud.create_user(db, email=user.email, password=user.password)

@router.post("/login", response_model=schemas.TokenResponse)
def login(login_request: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login and get JWT token"""
    db_user = crud.get_user_by_email(db, email=login_request.email)
    if not db_user or not auth.verify_password(login_request.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(db_user.id)},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user info (requires auth token)"""
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/me", response_model=schemas.UserResponse)
def update_current_user(
    update_request: schemas.UserUpdateRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user(db, user, name=update_request.name)

@router.delete("/me", response_model=schemas.MessageResponse)
def delete_current_user(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(db, user)
    return {"message": "User account deleted successfully."}
