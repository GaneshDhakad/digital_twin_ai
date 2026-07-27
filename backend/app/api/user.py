from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.dependencies import get_db,get_current_user
from app.crud.user import create_user
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/", response_model=UserResponse)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    return create_user(db, user)

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user    