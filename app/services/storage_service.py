from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

import oss2  # type: ignore

from app.core.config import settings


@dataclass
class TempLink:
    url: str
    expires_at: datetime


class StorageBackend(Protocol):
    async def upload(self, path: str, data: bytes) -> str:  # returns storage path or url
        ...

    async def download(self, path: str) -> bytes:
        ...

    async def generate_temp_link(self, path: str, expires_seconds: int | None = None) -> TempLink:
        ...


class LocalStorageBackend:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    async def upload(self, path: str, data: bytes) -> str:
        full_path = os.path.join(self.base_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        return path

    async def download(self, path: str) -> bytes:
        full_path = os.path.join(self.base_dir, path)
        with open(full_path, "rb") as f:
            return f.read()

    async def generate_temp_link(self, path: str, expires_seconds: int | None = None) -> TempLink:
        # For local, we just return a file path reference; serving should be handled by an API endpoint.
        if expires_seconds is None:
            expires_seconds = settings.TEMP_URL_EXPIRES_SECONDS
        return TempLink(url=f"local://{path}", expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_seconds))


class OSSStorageBackend:
    def __init__(self) -> None:
        if not all(
            [
                settings.OSS_ENDPOINT,
                settings.OSS_BUCKET,
                settings.OSS_ACCESS_KEY_ID,
                settings.OSS_ACCESS_KEY_SECRET,
            ]
        ):
            raise RuntimeError("OSS credentials are not fully configured")
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET)

    async def upload(self, path: str, data: bytes) -> str:
        self.bucket.put_object(path, data)
        return path

    async def download(self, path: str) -> bytes:
        result = self.bucket.get_object(path)
        try:
            return result.read()
        finally:
            result.close()

    async def generate_temp_link(self, path: str, expires_seconds: int | None = None) -> TempLink:
        if expires_seconds is None:
            expires_seconds = settings.TEMP_URL_EXPIRES_SECONDS
        signed_url = self.bucket.sign_url("GET", path, expires_seconds)
        return TempLink(url=signed_url, expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_seconds))


def get_storage_backend() -> StorageBackend:
    if settings.STORAGE_BACKEND == "oss":
        return OSSStorageBackend()
    return LocalStorageBackend(settings.LOCAL_STORAGE_DIR)
