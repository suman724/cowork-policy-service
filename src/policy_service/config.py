"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "dev"
    log_level: str = "info"
    config_dir: str = "config"
    policy_expiry_hours: int = 24
    schema_version: str = "1.0"

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}
