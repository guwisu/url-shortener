from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl, FutureDatetime


class LinkCreate(BaseModel):
    url: HttpUrl
    expires_at: FutureDatetime | None = None

class LinkResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    created_at: datetime
    clicks_count: int
    is_active: bool
    expires_at: datetime | None
    
    model_config = ConfigDict(from_attributes=True)
