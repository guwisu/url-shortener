from sqlalchemy import insert, select

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
        model = result.scalar_one()
        return model


    async def get_by_code(self, code: str) -> Link | None:
        query = select(self.model).where(self.model.short_code==code)

        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model