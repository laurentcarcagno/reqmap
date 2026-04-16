"""ReqMap FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routers import health, customers, documents, nodes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("ReqMap API started")
    yield
    await engine.dispose()
    logger.info("ReqMap API stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(customers.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(nodes.router, prefix="/api/v1")

    return app


app = create_app()
