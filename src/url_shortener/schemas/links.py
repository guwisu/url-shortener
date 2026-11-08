import ipaddress
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FutureDatetime,
    HttpUrl,
    field_validator,
)


class LinkCreate(BaseModel):
    url: HttpUrl = Field(max_length=2048)
    expires_at: FutureDatetime | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, url: HttpUrl):
        host = (url.host or "").lower().rstrip(".")
        if host == "localhost" or host.endswith(".localhost"):
            raise ValueError("Private and local URLs are not allowed")
        try:
            ip = ipaddress.ip_address(host.strip("[]"))
        except ValueError:
            return url
        if not ip.is_global:
            raise ValueError("Non-public IP addresses are not allowed")
        return url


class LinkPublic(BaseModel):
    original_url: str
    short_code: str
    clicks_count: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class LinkResponse(LinkPublic):
    id: int
    user_id: int
    created_at: datetime
    expires_at: datetime | None


class RedirectResponse(BaseModel):
    original_url: str
