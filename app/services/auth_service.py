from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.utils.password import verify_password, hash_password


class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, username_or_email: str, password: str) -> Optional[User]:
        stmt = select(User).where(
            (User.username == username_or_email) | (User.email == username_or_email)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def create_token_pair(subject: str | int) -> tuple[str, str, int]:
        now = datetime.now(timezone.utc)
        access_exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_exp = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload_base = {
            "sub": str(subject),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "iat": int(now.timestamp()),
        }
        access_token = jwt.encode(
            {**payload_base, "exp": int(access_exp.timestamp())},
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        refresh_token = jwt.encode(
            {**payload_base, "type": "refresh", "exp": int(refresh_exp.timestamp())},
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return access_token, refresh_token, int(access_exp.timestamp())

    @staticmethod
    async def register_user(db: AsyncSession, username: str, email: str, password: str) -> User:
        user = User(username=username, email=email, password_hash=hash_password(password))
        db.add(user)
        await db.flush()
        return user
