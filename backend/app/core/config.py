"""
CineMetrics — Production Application Configuration
Loads environment variables and application settings using Pydantic Settings.
"""

import socket
import logging
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("Config")
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


def is_postgres_available(host: str = "localhost", port: int = 5432, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


class Settings(BaseSettings):
    PROJECT_NAME: str = "CineMetrics"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database Configuration
    DATABASE_URL: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Currency Exchange Reference
    DEFAULT_INR_USD_RATE: float = 83.50

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_SIMULATION: str = "30/minute"

    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "*",
    ]

    # Model & Data Paths
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "ml" / "models" / "production"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    UNIFIED_DIR: Path = BASE_DIR / "data" / "unified"

    @property
    def sync_database_url(self) -> str:
        """
        Returns sync database URL.
        Falls back automatically to SQLite if PostgreSQL is unreachable or not configured.
        """
        sqlite_fallback = f"sqlite:///{BASE_DIR / 'cinemetrics.db'}"

        if not self.DATABASE_URL:
            return sqlite_fallback

        if "sqlite" in self.DATABASE_URL:
            return self.DATABASE_URL

        # Check if PostgreSQL service is actively running
        if not is_postgres_available(self.POSTGRES_HOST, self.POSTGRES_PORT):
            return sqlite_fallback

        # Normalize asyncpg to standard postgresql sync driver
        url = self.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://")
        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
