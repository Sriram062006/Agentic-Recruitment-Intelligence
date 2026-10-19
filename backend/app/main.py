"""
FastAPI application factory and bootstrap module.
Configures middleware, logging, routers, and OpenAPI documentation.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory that configures and returns a FastAPI instance."""
    if settings is None:
        settings = get_settings()

    # Initialize structured logging
    configure_logging(level=settings.log_level)
    logger = get_logger("bootstrap")
    logger.info("Initializing %s in [%s] mode", settings.app_name, settings.app_env)

    app = FastAPI(
        title=settings.app_name,
        description="Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS for local development - restrict strictly to configured origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "X-Request-ID"],
    )

    # Register API routers under /api
    app.include_router(api_router, prefix="/api")

    logger.info("FastAPI application initialized successfully")
    return app


# ASGI application instance for uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
