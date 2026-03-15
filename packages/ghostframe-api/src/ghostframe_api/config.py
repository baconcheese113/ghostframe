"""Application settings via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "GhostFrame"
    debug: bool = False

    model_config = {"env_prefix": "GHOSTFRAME_"}
