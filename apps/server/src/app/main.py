"""Main application entry point."""
# ruff: noqa: I001

import os

from contextlib import asynccontextmanager

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from app.settings import get_settings
from app.auth import create_access_token, verify_token


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="A Python API built with Better Fullstack",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN") or "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to gaspirator!"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Auth endpoints
@app.post("/auth/token")
async def login(username: str = "", password: str = ""):
    """Create an access token."""
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    token = create_access_token(data={"sub": username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me")
async def get_current_user(authorization: str = Header(default="")):
    """Get the current authenticated user from a Bearer token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"username": payload.get("sub"), "token_data": payload}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
