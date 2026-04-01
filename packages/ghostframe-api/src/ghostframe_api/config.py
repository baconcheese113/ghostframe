"""Application settings via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings

# Repo root when running from source; overridden by env vars in deployment
_DEFAULT_DEMO_MAF = Path(__file__).parents[4] / "data" / "demo" / "2b06dd99-f6e0-49d1-984e-28564673c8e2.wxs.aliquot_ensemble_masked.maf"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "GhostFrame"
    debug: bool = False
    demo_maf: Path = _DEFAULT_DEMO_MAF

    model_config = {"env_prefix": "GHOSTFRAME_"}
