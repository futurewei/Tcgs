from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.MEMBER


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    id: int
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
