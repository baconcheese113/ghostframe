"""Dependency injection for FastAPI routes."""

from ghostframe_api.config import Settings


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
