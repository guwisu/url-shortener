from datetime import datetime

from sqlalchemy import insert, select, update

from url_shortener.models import Link
from url_shortener.repositories.base import BaseRepository


class LinkRepository(BaseRepository[Link]):
    model = Link

    async def add(self, original_url: str, short_code: str, expires_at: datetime | None = None) -> Link:
        stmt = insert(self.model).values(
            original_url=original_url, 
            short_code=short_code,
            expires_at=expires_at,
        ).returning(self.model)

        result = await self.session.execute(stmt)
        return result.scalar_one()


    async def get_by_code(self, code: str) -> Link | None:
        query = select(self.model).where(self.model.short_code==code)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def increment_clicks(self, code: str) -> None:
        stmt = (
            update(self.model)
            .where(self.model.short_code == code)
            .values(clicks_count=self.model.clicks_count + 1)
        )
        await self.session.execute(stmt)