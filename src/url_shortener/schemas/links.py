from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LinkCreate(BaseModel):
    url: str


class LinkResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    created_at: datetime
    clicks_count: int

    model_config = ConfigDict(from_attributes=True)
