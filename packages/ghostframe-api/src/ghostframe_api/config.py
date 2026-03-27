"""Application settings via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings

# Repo root when running from source; overridden by GHOSTFRAME_DEMO_FASTA in deployment
_DEFAULT_DEMO_FASTA = Path(__file__).parents[4] / "data" / "demo" / "hpv16_k02718.fasta"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "GhostFrame"
    debug: bool = False
    demo_fasta: Path = _DEFAULT_DEMO_FASTA

    model_config = {"env_prefix": "GHOSTFRAME_"}
