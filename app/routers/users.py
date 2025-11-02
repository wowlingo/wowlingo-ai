from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.common.database import get_db
from app.models.wowlingo_models import User
from app.common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: str = None
    metadata: dict = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str = None
    is_active: bool
    metadata: dict = None

    class Config:
        from_attributes = True


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/", response_model=List[UserResponse])
async def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create new user"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    db_user = User(
        username=user.username,
        email=user.email,
        metadata=user.metadata
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info(f"Created new user: {user.username}")
    return db_user