from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True