"""FastAPI application factory and module-level app instance."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ghostframe_api.routes import analysis, health


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="GhostFrame API",
        description="Multi-frame variant impact scanner with neoantigen scoring",
        version="0.1.0",
    )

    # GHOSTFRAME_CORS_ORIGINS: comma-separated list of allowed origins.
    # Defaults to "*" for local dev; set to the Vercel URL in production.
    origins = os.getenv("GHOSTFRAME_CORS_ORIGINS", "*").split(",")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(analysis.router, prefix="/api")

    return application


app = create_app()
