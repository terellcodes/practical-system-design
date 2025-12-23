"""
Shared response models

Used by all services for consistent API responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Generic message response for operations"""
    message: str
    id: Optional[str] = Field(None, description="Related resource ID (if applicable)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "id": "123"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoints"""
    status: str = Field(..., description="Overall health status: healthy, degraded, unhealthy")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Health check timestamp")
    dependencies: Dict[str, Any] = Field(default_factory=dict, description="Status of dependencies")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "user-service",
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00",
                "dependencies": {
                    "postgres": "healthy",
                    "redis": "healthy"
                }
            }
        }

