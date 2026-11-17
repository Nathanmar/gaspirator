"""Main application entry point."""
# ruff: noqa: I001

import os

from contextlib import asynccontextmanager

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.settings import get_settings
from app.db import ConcurrencyLimit
from app.errors import ApiError, api_error_handler, validation_exception_handler
from app import admin, auth_routes, lots, profile, registration, reservations, suppliers


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="A platform that connects food suppliers (canteens, hospitals, supermarkets…) with charities, so surplus food is donated instead of thrown away.",
    version="0.1.0",
    lifespan=lifespan,
)

# Inside CORS (the last middleware added is the outermost): never more requests to the API
# in flight than database connections, see app.db.ConcurrencyLimit.
app.add_middleware(ConcurrencyLimit, path_prefix=f"{settings.api_prefix}/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN") or "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ApiError, api_error_handler)

# Contract routes (openapi.yaml, server url: /api/v1)
app.include_router(registration.router, prefix="/api/v1")
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(lots.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(reservations.router, prefix="/api/v1")
app.include_router(suppliers.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to gaspirator!"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
