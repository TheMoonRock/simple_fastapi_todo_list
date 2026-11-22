from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import Priority, Status


class TodoBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    status: Status = Status.PENDING
    deadline: Optional[datetime] = None


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    deadline: Optional[datetime] = None


class TodoOut(TodoBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}