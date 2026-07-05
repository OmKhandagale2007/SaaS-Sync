"""
Centralized configuration, loaded from environment variables / .env file.

Why this pattern: hardcoding secrets or DB URLs in code is a common beginner
mistake. Reading them from the environment means the exact same code can run
against SQLite on your laptop and Postgres in production, with zero code
changes -- just a different .env.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "sqlite:///./syncline.db"

    # Auth
    jwt_secret: str = "change-this-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # CORS
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    # HubSpot
    hubspot_client_id: str = ""
    hubspot_client_secret: str = ""
    hubspot_redirect_uri: str = "http://localhost:8000/api/integrations/hubspot/callback"

    # QuickBooks
    quickbooks_client_id: str = ""
    quickbooks_client_secret: str = ""
    quickbooks_redirect_uri: str = "http://localhost:8000/api/integrations/quickbooks/callback"
    quickbooks_environment: str = "sandbox"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
