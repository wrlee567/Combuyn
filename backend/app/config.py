"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Combuyn"
    environment: str = "development"

    # SQLAlchemy URL. Defaults to local docker-compose Postgres.
    # On Render this is supplied via the DATABASE_URL env var.
    database_url: str = "postgresql+psycopg://combuyn:combuyn@localhost:5432/combuyn"

    # Comma-separated list of allowed CORS origins for the React frontend.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Seed the database with the bundled CCF reference data on startup.
    seed_on_startup: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
