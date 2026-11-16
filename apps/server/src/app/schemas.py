"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field


# Example request/response schemas
class ItemCreate(BaseModel):
    """Schema for creating an item."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: str | None = Field(None, max_length=500, description="Item description")
    price: float = Field(..., gt=0, description="Item price (must be positive)")
    quantity: int = Field(default=1, ge=0, description="Item quantity")


class ItemResponse(BaseModel):
    """Schema for item response."""

    id: int
    name: str
    description: str | None
    price: float
    quantity: int


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    email: EmailStr = Field(..., description="Sender email address")
    subject: str = Field(..., min_length=1, max_length=200, description="Message subject")
    content: str = Field(..., min_length=1, description="Message content")


class MessageResponse(BaseModel):
    """Schema for message response."""

    success: bool
    message: str
