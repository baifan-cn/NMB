from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    PROJECT_NAME: str = "新闻杂志管理系统"
    VERSION: str = "0.1.0"

    API_V1_PREFIX: str = "/api/v1"

    # 默认本地开发使用 SQLite（异步驱动 aiosqlite），生产/测试可通过环境变量切换到 MySQL
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    JWT_ISSUER: str = "nmb-api"
    JWT_AUDIENCE: str = "nmb-clients"
    PASSWORD_HASH_SCHEME: str = "argon2"

    AUTO_CREATE_TABLES: bool = True  # dev convenience

    # Storage configuration
    STORAGE_BACKEND: str = "local"  # options: 'oss' | 'local'
    LOCAL_STORAGE_DIR: str = "storage"

    OSS_BUCKET: str = ""
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""

    # Alipay configuration
    ALIPAY_APP_ID: str = ""
    ALIPAY_PUBLIC_KEY: str = ""  # PEM format including header/footer
    ALIPAY_SIGN_TYPE: str = "RSA2"  # RSA2 required
    ALIPAY_APP_PRIVATE_KEY: str = ""  # PEM format including header/footer
    ALIPAY_GATEWAY: str = "https://openapi.alipay.com/gateway.do"
    ALIPAY_NOTIFY_URL: str = ""
    ALIPAY_RETURN_URL: str = ""

    # OAuth providers
    WECHAT_CLIENT_ID: str = ""
    WECHAT_CLIENT_SECRET: str = ""
    WECHAT_REDIRECT_URI: str = ""
    WECHAT_SCOPE: str = "snsapi_login"

    WEIBO_CLIENT_ID: str = ""
    WEIBO_CLIENT_SECRET: str = ""
    WEIBO_REDIRECT_URI: str = ""
    WEIBO_SCOPE: str = ""

    DOUYIN_CLIENT_KEY: str = ""
    DOUYIN_CLIENT_SECRET: str = ""
    DOUYIN_REDIRECT_URI: str = ""
    DOUYIN_SCOPE: str = "user_info"

    # File encryption
    FILE_CRYPT_MASTER_KEY: str = "change-me-please"
    TEMP_URL_EXPIRES_SECONDS: int = 3600

    # Login throttle & lockout
    LOGIN_FAIL_LIMIT: int = 5
    LOGIN_LOCK_MINUTES: int = 15
    LOGIN_FAIL_WINDOW_SECONDS: int = 15 * 60


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
