from fastapi import APIRouter, Depends, HTTPException, status
from slowapi.util import get_remote_address
from app.core.rate_limit import limiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.auth import LoginIn, RegisterIn, TokenPair, ProfileOut, ProfileUpdateIn, ChangePasswordIn
from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService
from app.services.audit_service import AuditService
from app.utils.password import verify_password, hash_password
from app.models.user import User
from app.models.social_account import SocialAccount
from sqlalchemy import select, delete
from app.utils.security import create_access_token
from app.core.config import settings
from jose import jwt, JWTError

router = APIRouter()
oauth_service = OAuthService()


@router.post("/register", response_model=ProfileOut)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)) -> ProfileOut:
    existing = await db.execute(
        User.__table__.select().where((User.username == payload.username) | (User.email == payload.email))
    )
    row = existing.first()
    if row:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = await AuthService.register_user(db, payload.username, payload.email, payload.password)
    await db.commit()
    return ProfileOut.model_validate(user)


@router.post("/login", response_model=TokenPair)
@limiter.limit("5/minute")
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)) -> TokenPair:
    user = await AuthService.authenticate(db, payload.username_or_email, payload.password)
    if user is None:
        # do not reveal lock or existence; generic response
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token, refresh_token, exp = AuthService.create_token_pair(user.id)
    await AuditService.log(db, user_id=user.id, action="login.success")
    await db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token, expires_in=exp)


@router.post("/refresh-token", response_model=TokenPair)
@limiter.limit("10/minute")
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)) -> TokenPair:
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM], audience=settings.JWT_AUDIENCE, issuer=settings.JWT_ISSUER
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    access_token, new_refresh_token, exp = AuthService.create_token_pair(user_id)
    return TokenPair(access_token=access_token, refresh_token=new_refresh_token, expires_in=exp)


def _get_current_user_from_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM], audience=settings.JWT_AUDIENCE, issuer=settings.JWT_ISSUER
        )
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")


@router.get("/profile", response_model=ProfileOut)
async def profile(authorization: str, db: AsyncSession = Depends(get_db)) -> ProfileOut:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    user_id = _get_current_user_from_token(authorization.split()[1])
    result = await db.get(User, int(user_id))
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return ProfileOut.model_validate(result)


@router.put("/profile", response_model=ProfileOut)
async def update_profile(payload: ProfileUpdateIn, authorization: str, db: AsyncSession = Depends(get_db)) -> ProfileOut:
    user_id = _get_current_user_from_token(authorization.split()[1])
    user = await db.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.username:
        user.username = payload.username
    await db.commit()
    await db.refresh(user)
    return ProfileOut.model_validate(user)


@router.put("/change-password")
async def change_password(payload: ChangePasswordIn, authorization: str, db: AsyncSession = Depends(get_db)) -> dict:
    user_id = _get_current_user_from_token(authorization.split()[1])
    user = await db.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Old password incorrect")
    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    await AuditService.log(db, user_id=user.id, action="password.change")
    await db.commit()
    return {"message": "Password changed"}


@router.post("/logout")
async def logout(refresh_token: str | None = None) -> dict:
    # Placeholder: In future, store refresh token jti in blacklist/rotate tokens
    # TODO: add refresh token blacklist
    return {"message": "Logged out"}


def _validate_provider(provider: str) -> None:
    if provider not in {"wechat", "weibo", "douyin"}:
        raise HTTPException(status_code=400, detail="Unsupported provider")


def _ensure_provider_config(provider: str) -> None:
    cfg = settings
    if provider == "wechat" and (not cfg.WECHAT_CLIENT_ID or not cfg.WECHAT_CLIENT_SECRET or not cfg.WECHAT_REDIRECT_URI):
        raise HTTPException(status_code=400, detail="WeChat OAuth not configured")
    if provider == "weibo" and (not cfg.WEIBO_CLIENT_ID or not cfg.WEIBO_CLIENT_SECRET or not cfg.WEIBO_REDIRECT_URI):
        raise HTTPException(status_code=400, detail="Weibo OAuth not configured")
    if provider == "douyin" and (not cfg.DOUYIN_CLIENT_KEY or not cfg.DOUYIN_CLIENT_SECRET or not cfg.DOUYIN_REDIRECT_URI):
        raise HTTPException(status_code=400, detail="Douyin OAuth not configured")


@router.get("/oauth/{provider}/authorize")
@limiter.limit("20/minute")
async def oauth_authorize(provider: str) -> dict:
    _validate_provider(provider)
    _ensure_provider_config(provider)
    auth = await oauth_service.authorize_url(provider)  # type: ignore[arg-type]
    return {"authorize_url": auth.url, "state": auth.state}


@router.get("/oauth/{provider}/callback")
@limiter.limit("20/minute")
async def oauth_callback(provider: str, code: str, state: str, authorization: str | None = None, db: AsyncSession = Depends(get_db)) -> dict:
    _validate_provider(provider)
    _ensure_provider_config(provider)
    current_user_id: int | None = None
    if authorization and authorization.lower().startswith("bearer "):
        try:
            current_user_id = int(_get_current_user_from_token(authorization.split()[1]))
        except Exception:
            current_user_id = None
    try:
        user, _ = await oauth_service.handle_callback(db, provider, code, state, current_user_id)  # type: ignore[arg-type]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=400, detail="OAuth callback failed")
    access_token, refresh_token, exp = AuthService.create_token_pair(user.id)
    await AuditService.log(db, user_id=user.id, action=f"oauth.{provider}.login")
    await db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "expires_in": exp}


@router.delete("/oauth/{provider}")
async def oauth_unbind(provider: str, authorization: str, db: AsyncSession = Depends(get_db)) -> dict:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    user_id = int(_get_current_user_from_token(authorization.split()[1]))
    # Ensure binding exists
    stmt = select(SocialAccount).where(
        (SocialAccount.provider == provider) & (SocialAccount.user_id == user_id)
    )
    result = await db.execute(stmt)
    social = result.scalar_one_or_none()
    if social is None:
        raise HTTPException(status_code=404, detail="Binding not found")
    await db.execute(
        delete(SocialAccount).where(
            (SocialAccount.provider == provider) & (SocialAccount.user_id == user_id)
        )
    )
    await AuditService.log(db, user_id=user_id, action=f"oauth.{provider}.unbind")
    await db.commit()
    return {"message": "Unbound"}


@router.get("/oauth/bindings")
async def oauth_bindings(authorization: str, db: AsyncSession = Depends(get_db)) -> dict:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    user_id = int(_get_current_user_from_token(authorization.split()[1]))
    stmt = select(SocialAccount.provider).where(SocialAccount.user_id == user_id)
    result = await db.execute(stmt)
    providers = [row[0] for row in result.fetchall()]
    return {"providers": providers}
