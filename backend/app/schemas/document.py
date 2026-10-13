import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    file_size: str
    content_type: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True 