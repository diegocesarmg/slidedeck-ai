"""Application configuration via environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings loaded from env vars / .env file."""

    # ── API Keys ─────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ── LLM Provider ────────────────────────────────────────────────────
    LLM_PROVIDER: str = "gemini"  # "gemini" | "openai" | "claude"

    # ── Paths ────────────────────────────────────────────────────────────
    OUTPUT_DIR: Path = Path("/tmp/slidedeck-ai/output")

    # ── App ──────────────────────────────────────────────────────────────
    APP_TITLE: str = "SlideDeck AI API"
    DEBUG: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton for app settings."""
    return Settings()
