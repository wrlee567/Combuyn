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

    # Seed immutable reference data (frameworks, controls, ISO 42001 catalog)
    # on startup. Safe for production.
    seed_on_startup: bool = True

    # Seed sample/demo records (example vendors, AI systems, trust-center data).
    # MUST stay false in production — these are illustrative, not real data.
    seed_demo_data: bool = False

    # JWT bearer auth. Tokens carry an ``org_id`` claim used for tenant scoping.
    # MUST be overridden with a strong secret in production.
    jwt_secret: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"

    # Create tables via Base.metadata.create_all on startup. Convenient for
    # local/test, but production should run Alembic migrations instead. When
    # unset, defaults to on outside production.
    auto_create_schema: bool | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def create_schema_on_startup(self) -> bool:
        if self.auto_create_schema is not None:
            return self.auto_create_schema
        return self.environment.lower() not in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
