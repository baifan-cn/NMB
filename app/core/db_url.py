from __future__ import annotations


def normalize_database_url(url: str) -> str:
    if not url:
        return url
    # SQLite
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    if url.startswith("sqlite://") and "+aiosqlite" not in url:
        return url.replace("sqlite://", "sqlite+aiosqlite://")

    # MySQL (prefer aiomysql for async)
    if url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+aiomysql://")
    if url.startswith("mysql+pymysql://"):
        return url.replace("mysql+pymysql://", "mysql+aiomysql://")

    # PostgreSQL (prefer asyncpg)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://")
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://")

    return url
