from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ClickEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    short_code: str
    timestamp: datetime
    ip_hash: str
    referer: str | None = None
    user_agent: str | None = None