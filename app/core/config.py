from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    APP_NAME: str = "Vechnaya Pamyat API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # CORS (comma-separated origins)
    BACKEND_CORS_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500"

    # Core PostgreSQL (operational DB)
    CORE_DB_HOST: str = "core-db"
    CORE_DB_PORT: int = 5432
    CORE_DB_USER: str = "core_user"
    CORE_DB_PASSWORD: str = "core_pass"
    CORE_DB_NAME: str = "core_db"

    # Analytics PostgreSQL (analytics / audit)
    ANALYTICS_DB_HOST: str = "analytics-db"
    ANALYTICS_DB_PORT: int = 5432
    ANALYTICS_DB_USER: str = "analytics_user"
    ANALYTICS_DB_PASSWORD: str = "analytics_pass"
    ANALYTICS_DB_NAME: str = "analytics_db"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def core_db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.CORE_DB_USER}:{self.CORE_DB_PASSWORD}"
            f"@{self.CORE_DB_HOST}:{self.CORE_DB_PORT}/{self.CORE_DB_NAME}"
        )

    @property
    def core_db_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.CORE_DB_USER}:{self.CORE_DB_PASSWORD}"
            f"@{self.CORE_DB_HOST}:{self.CORE_DB_PORT}/{self.CORE_DB_NAME}"
        )

    @property
    def analytics_db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.ANALYTICS_DB_USER}:{self.ANALYTICS_DB_PASSWORD}"
            f"@{self.ANALYTICS_DB_HOST}:{self.ANALYTICS_DB_PORT}/{self.ANALYTICS_DB_NAME}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
