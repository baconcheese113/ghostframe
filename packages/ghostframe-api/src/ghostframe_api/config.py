"""Application settings via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings

# Repo root when running from source; overridden by env vars in deployment
_DEFAULT_DEMO_FASTA = Path(__file__).parents[4] / "data" / "demo" / "hpv16_k02718.fasta"
_DEFAULT_DEMO_MAF = Path(__file__).parents[4] / "data" / "demo" / "sample.maf"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "GhostFrame"
    debug: bool = False
    demo_fasta: Path = _DEFAULT_DEMO_FASTA
    demo_maf: Path = _DEFAULT_DEMO_MAF

    model_config = {"env_prefix": "GHOSTFRAME_"}
