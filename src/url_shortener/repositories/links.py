from sqlalchemy import insert, select, update

from url_shortener.models import Link
from url_shortener.repositories.base import BaseRepository


class LinkRepository(BaseRepository):
    model = Link

    async def add(self, original_url: str, short_code: str) -> Link:
        stmt = insert(self.model).values(
            original_url=original_url, 
            short_code=short_code
        ).returning(self.model)

        result = await self.session.execute(stmt)
        return result.scalar_one()


    async def get_by_code(self, code: str) -> Link | None:
        query = select(self.model).where(self.model.short_code==code)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_and_increment_clicks(self, code: str) -> Link | None:
        stmt = (
            update(self.model)
            .where(self.model.short_code == code)
            .values(clicks_count=self.model.clicks_count + 1)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()