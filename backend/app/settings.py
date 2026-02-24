from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"
_DEFAULT_DB = f"sqlite:///{_BACKEND_DIR / 'lcs_dev.db'}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), env_file_encoding="utf-8")

    # Database
    database_url: str = _DEFAULT_DB

    # Auth
    jwt_secret_key: str = "change-this-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Anthropic / AI (primary)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    chat_max_tokens: int = 1024
    chat_history_limit: int = 20

    # OpenAI (fallback - optional)
    openai_api_key: Optional[str] = None

    # External APIs
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    polygon_api_key: str = ""
    kalshi_api_key: Optional[str] = None
    fred_api_key: Optional[str] = None

    # App settings
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
