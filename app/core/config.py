from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    PROJECT_NAME: str = "新闻杂志管理系统"
    VERSION: str = "0.1.0"

    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "mysql+pymysql://user:pass@localhost:3306/magazine_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    OSS_BUCKET: str = ""
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
