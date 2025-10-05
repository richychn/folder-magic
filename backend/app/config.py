import os
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from the project .env (if present)
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """Runtime configuration loaded from the environment."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_name: str = "Repository Drive Explorer"
    backend_origin: str = "http://localhost:8000"
    frontend_origin: str = "http://localhost:5173"
    session_cookie_name: str = "session_id"
    session_cookie_max_age: int = 60 * 60 * 24
    session_cookie_secure: bool = False
    session_secret_key: str = "dev-session-secret-change-me"
    google_client_id: str
    google_client_secret: str
    google_scopes: List[str] = (
        "openid email profile https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/drive".split()
    )
    google_picker_api_key: str | None = None
    session_cleanup_seconds: int = 60 * 60 * 12
    allowed_origins: List[str] = []

    @field_validator(
        "backend_origin",
        "frontend_origin",
        "session_cookie_name",
        "session_secret_key",
        "google_picker_api_key",
        mode="before",
    )
    @classmethod
    def _read_env_overrides(cls, value: str | None, info):  # type: ignore[override]
        env_value = os.getenv(info.field_name.upper())
        return env_value if env_value is not None else value

    @field_validator("session_cookie_max_age", "session_cleanup_seconds", mode="before")
    @classmethod
    def _convert_numeric(cls, value: int | str, info):  # type: ignore[override]
        env_value = os.getenv(info.field_name.upper())
        raw = env_value if env_value is not None else value
        return int(raw)

    @field_validator("session_cookie_secure", mode="before")
    @classmethod
    def _convert_bool(cls, value: bool | str):  # type: ignore[override]
        if isinstance(value, bool):
            return value
        return str(value).lower() == "true"

    @field_validator("google_scopes", mode="before")
    @classmethod
    def _split_scopes(cls, value: List[str] | str):  # type: ignore[override]
        if isinstance(value, list):
            return value
        env_value = os.getenv("GOOGLE_SCOPES")
        raw = env_value if env_value is not None else value
        if isinstance(raw, str):
            return [scope for scope in raw.split() if scope]
        return raw

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _populate_allowed_origins(cls, value: List[str] | None):  # type: ignore[override]
        raw = os.getenv("BACKEND_ALLOWED_ORIGINS")
        if raw:
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        return value or []

    @field_validator("google_client_id", "google_client_secret", "session_secret_key")
    @classmethod
    def _ensure_not_empty(cls, value: str, info):  # type: ignore[override]
        if not value:
            raise ValueError(f"{info.field_name.upper()} must be configured in the environment")
        return value

    def resolved_origins(self) -> List[str]:
        origins = set(self.allowed_origins)
        origins.add(self.frontend_origin)
        return list(origins)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""

    return Settings()
