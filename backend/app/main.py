"""
CineMetrics — Production FastAPI Application Core
Initializes FastAPI, CORS middleware, Slowapi rate limiting, RFC-7807 error handlers,
and database hydration lifecycle hooks.
"""

import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.app.core.config import settings
from backend.app.db.init_db import init_db
from backend.app.api.v1.api import api_router
from backend.app.ml.explainer_service import explainer_service

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("CineMetricsAPI")

# Rate Limiter Configuration
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle management.
    """
    logger.info("Starting CineMetrics API server...")
    t0 = time.perf_counter()

    # 1. Initialize Database & Seed if empty
    try:
        init_db(force_reseed=False)
        logger.info("Database verified and catalog ready.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")

    # 2. Warm up ML Explainer Service
    _ = explainer_service
    logger.info(f"CineMetrics API successfully initialized in {(time.perf_counter() - t0):.2f}s.")

    yield

    logger.info("Shutting down CineMetrics API server...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Movie Revenue Prediction, Box-Office Forecasting & Cinema Intelligence Platform.",
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Attach state for slowapi
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Standard Error Handlers (RFC-7807 Compliant)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://errors.cinemetrics.ai/validation-error",
            "title": "Unprocessable Entity",
            "status": 422,
            "detail": exc.errors(),
            "instance": str(request.url),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://errors.cinemetrics.ai/internal-server-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An internal server error occurred. Please contact system support.",
            "instance": str(request.url),
        },
    )


# Performance Header Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    response.headers["X-Process-Time-Ms"] = str(process_time_ms)
    return response


# Root Landing Endpoint
@app.get("/", summary="Root Health & Documentation Landing")
def root_landing():
    return {
        "service": "CineMetrics API",
        "status": "online",
        "version": settings.PROJECT_VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_v1": settings.API_V1_STR,
    }


# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

