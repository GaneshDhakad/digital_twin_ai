from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fastapi.security import OAuth2PasswordRequestForm
from app.core.dependencies import get_db
from app.core.security import create_access_token
from app.crud.auth import authenticate_user
from app.schemas.auth import LoginRequest, Token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


from fastapi import HTTPException, status

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    token = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return token