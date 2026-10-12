from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PG_DB: str
    PG_USER: str
    PG_PASSWORD: str
    PG_PORT: str
    PG_HOST: str


    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()