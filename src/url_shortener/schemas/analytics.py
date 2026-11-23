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


class DailyClicks(BaseModel):
    date: str
    clicks: int


class RefererStat(BaseModel):
    referer: str
    clicks: int


class DeviceStat(BaseModel):
    device: str
    clicks: int


class LinkStatsResponse(BaseModel):
    short_code: str
    total_clicks: int
    by_day: list[DailyClicks]
    top_referers: list[RefererStat]
    devices: list[DeviceStat]
