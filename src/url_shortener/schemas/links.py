from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, FutureDatetime, HttpUrl


class LinkCreate(BaseModel):
    url: HttpUrl = Field(max_length=2048)
    expires_at: FutureDatetime | None = None


class LinkPublic(BaseModel):
    id: int
    user_id: int
    original_url: str
    short_code: str
    created_at: datetime
    clicks_count: int
    is_active: bool
    expires_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class LinkResponse(LinkPublic):
    id: int
    user_id: int
    created_at: datetime
    expires_at: datetime | None
