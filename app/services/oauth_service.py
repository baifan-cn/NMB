from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.social_account import SocialAccount
from app.models.user import User
from app.utils.redis_kv import RedisKV
from app.utils.password import hash_password

Provider = Literal["wechat", "weibo", "douyin"]


@dataclass
class OAuthAuthorizeURL:
    url: str
    state: str


class OAuthService:
    def __init__(self) -> None:
        self.redis = RedisKV()

    async def create_state(self, ttl_seconds: int = 300) -> str:
        state = secrets.token_urlsafe(24)
        await self.redis.set_json(f"oauth:state:{state}", {"ok": True}, ex=ttl_seconds)
        return state

    async def check_state(self, state: str) -> bool:
        key = f"oauth:state:{state}"
        exists = await self.redis.get_json(key)
        if exists:
            await self.redis.delete(key)
            return True
        return False

    def _client_for(self, provider: Provider) -> AsyncOAuth2Client:
        if provider == "wechat":
            return AsyncOAuth2Client(
                client_id=settings.WECHAT_CLIENT_ID,
                client_secret=settings.WECHAT_CLIENT_SECRET,
                redirect_uri=settings.WECHAT_REDIRECT_URI,
            )
        if provider == "weibo":
            return AsyncOAuth2Client(
                client_id=settings.WEIBO_CLIENT_ID,
                client_secret=settings.WEIBO_CLIENT_SECRET,
                redirect_uri=settings.WEIBO_REDIRECT_URI,
            )
        if provider == "douyin":
            return AsyncOAuth2Client(
                client_id=settings.DOUYIN_CLIENT_KEY,
                client_secret=settings.DOUYIN_CLIENT_SECRET,
                redirect_uri=settings.DOUYIN_REDIRECT_URI,
            )
        raise ValueError("unsupported provider")

    async def authorize_url(self, provider: Provider) -> OAuthAuthorizeURL:
        state = await self.create_state()
        client = self._client_for(provider)
        if provider == "wechat":
            # WeChat auth endpoint (Open Platform)
            url = client.create_authorization_url(
                "https://open.weixin.qq.com/connect/qrconnect",
                scope=settings.WECHAT_SCOPE,
                state=state,
                params={"response_type": "code"},
            )[0]
        elif provider == "weibo":
            url = client.create_authorization_url(
                "https://api.weibo.com/oauth2/authorize",
                scope=settings.WEIBO_SCOPE,
                state=state,
            )[0]
        else:  # douyin
            url = client.create_authorization_url(
                "https://open.douyin.com/platform/oauth/connect",
                scope=settings.DOUYIN_SCOPE,
                state=state,
            )[0]
        return OAuthAuthorizeURL(url=url, state=state)

    async def handle_callback(
        self, db: AsyncSession, provider: Provider, code: str, state: str, current_user_id: int | None
    ) -> tuple[User, SocialAccount]:
        if not await self.check_state(state):
            raise ValueError("invalid_state")
        client = self._client_for(provider)
        if provider == "wechat":
            token = await client.fetch_token(
                "https://api.weixin.qq.com/sns/oauth2/access_token",
                grant_type="authorization_code",
                code=code,
            )
            # userinfo
            resp = await client.get(
                "https://api.weixin.qq.com/sns/userinfo",
                params={"access_token": token["access_token"], "openid": token["openid"]},
            )
            data = resp.json()
            provider_user_id = data.get("unionid") or data.get("openid")
            nickname = data.get("nickname")
            avatar = data.get("headimgurl")
        elif provider == "weibo":
            token = await client.fetch_token(
                "https://api.weibo.com/oauth2/access_token",
                grant_type="authorization_code",
                code=code,
            )
            uid = token.get("uid")
            resp = await client.get(
                "https://api.weibo.com/2/users/show.json",
                params={"access_token": token["access_token"], "uid": uid},
            )
            data = resp.json()
            provider_user_id = str(uid)
            nickname = data.get("screen_name")
            avatar = data.get("profile_image_url")
        else:  # douyin
            token = await client.fetch_token(
                "https://open.douyin.com/oauth/access_token/",
                grant_type="authorization_code",
                code=code,
            )
            resp = await client.get(
                "https://open.douyin.com/oauth/userinfo/",
                params={"access_token": token["access_token"]},
            )
            data = resp.json().get("data", {})
            provider_user_id = data.get("union_id") or data.get("open_id")
            nickname = data.get("nickname")
            avatar = data.get("avatar")

        # find or create social account
        stmt = select(SocialAccount).where(
            (SocialAccount.provider == provider) & (SocialAccount.provider_user_id == str(provider_user_id))
        )
        result = await db.execute(stmt)
        social = result.scalar_one_or_none()

        if social is None:
            social = SocialAccount(
                provider=provider,
                provider_user_id=str(provider_user_id),
                union_id=data.get("unionid") if provider == "wechat" else data.get("union_id"),
                access_token=token.get("access_token"),
                refresh_token=token.get("refresh_token"),
                scope=token.get("scope"),
                nickname_snapshot=nickname,
                avatar_snapshot=avatar,
            )
            db.add(social)
            await db.flush()

        user: Optional[User] = None
        if social.user_id:
            user = await db.get(User, social.user_id)
        elif current_user_id:
            # bind to current user
            social.user_id = current_user_id
            user = await db.get(User, current_user_id)
        else:
            # auto-register user
            base_username = (nickname or provider).lower().replace(" ", "")
            username = f"{base_username}_{secrets.token_hex(4)}"
            email = f"{provider_user_id}@{provider}.oauth"
            user = User(username=username, email=email, password_hash=hash_password(secrets.token_urlsafe(12)))
            db.add(user)
            await db.flush()
            social.user_id = user.id

        await db.commit()
        await db.refresh(social)
        assert user is not None
        return user, social
