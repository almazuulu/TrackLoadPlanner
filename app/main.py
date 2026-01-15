from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routes import health, optimizer
from app.exceptions.handlers import (
    validation_exception_handler,
    generic_exception_handler
)

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for optimal truck load planning that maximizes carrier revenue "
                "while respecting weight, volume, hazmat, and route constraints.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register routes
# Health check at root level (/healthz)
app.include_router(health.router, tags=["Health"])

# API v1 routes
app.include_router(
    optimizer.router,
    prefix=settings.api_v1_prefix,
    tags=["Load Optimizer"]
)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirecting to API documentation."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/healthz"
    }
