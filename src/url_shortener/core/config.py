from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int = 5432
    POSTGRES_HOST: str = "localhost"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: list[str] = ["*"]

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    SYSTEM_WORDS: frozenset[str] = frozenset(
        {"api", "docs", "health", "redoc", "metrics"}
    )

    RATE_LIMIT_ENABLED: bool = True

    CELERY_BROKER_URL: str = "amqp://guest:guest@rabbitmq:5672//"

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CLICK_TOPIC: str = "clicks"
    ANALYTICS_SALT: str

    MONGO_DB: str = "url_shortener"
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017

    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def test_db_url(self) -> str:
        return (
            "postgresql+asyncpg://test_user:test_pass@localhost:5434/test_url_shortener"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def mongo_url(self) -> str:
        return f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]
