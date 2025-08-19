from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    username_or_email: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class ProfileOut(ORMModel):
    id: int
    username: str
    email: EmailStr
    status: str


class ProfileUpdateIn(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    avatar_url: str | None = None
    locale: str | None = None


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)
