from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import get_settings
from ..models.user import User
from ..schemas.user import LoginRequest, TokenResponse, UserResponse
from ..services.auth import AuthService, get_current_user

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # JWT is stateless, client should delete token
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
