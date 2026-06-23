from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Секреты, которые недопустимы вне режима отладки.
_INSECURE_JWT_SECRETS = {
    "",
    "change-me-in-production",
    "changeme",
    "secret",
    "test",
}


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
    # В продакшене ОБЯЗАТЕЛЬНО переопределить через переменную окружения JWT_SECRET_KEY.
    # Дефолт используется только в dev/debug — в проде валидатор ниже не даст запуститься.
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate limiting (login)
    # Максимум попыток входа с одного IP за окно.
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    # Длина окна в секундах.
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # YooKassa (https://yookassa.ru) — тестовый магазин.
    # Задаются через переменные окружения. Пустые значения = приём оплаты выключен.
    YOOKASSA_SHOP_ID: str = ""
    YOOKASSA_SECRET_KEY: str = ""
    # Куда ЮKassa вернёт пользователя после оплаты (страница фронтенда).
    YOOKASSA_RETURN_URL: str = "http://localhost:5500/client/payments.html"
    YOOKASSA_CURRENCY: str = "RUB"

    @property
    def is_production(self) -> bool:
        # Продакшен, если явно указано окружение или отключён DEBUG.
        return (
            self.APP_ENV.strip().lower() in {"production", "prod", "staging"}
            or not self.DEBUG
        )

    @model_validator(mode="after")
    def _enforce_secure_secret(self) -> "Settings":
        if self.is_production:
            secret = (self.JWT_SECRET_KEY or "").strip()
            if secret.lower() in _INSECURE_JWT_SECRETS or len(secret) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY должен быть задан надёжным уникальным значением "
                    "(не менее 32 символов) вне режима отладки. "
                    "Установите переменную окружения JWT_SECRET_KEY."
                )
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def yookassa_enabled(self) -> bool:
        # Приём оплаты доступен только когда заданы идентификатор магазина и ключ.
        return bool(self.YOOKASSA_SHOP_ID and self.YOOKASSA_SECRET_KEY)

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
