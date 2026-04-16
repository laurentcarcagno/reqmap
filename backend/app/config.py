"""Application configuration — all settings sourced from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_title: str = "ReqMap API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/reqmap.db"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # File upload
    upload_dir: Path = Path("uploads")
    max_upload_bytes: int = 52_428_800  # 50 MB

    # Customer config
    customers_config_path: Path = Path("config/customers.json")

    # JWT (Sprint 6)
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
