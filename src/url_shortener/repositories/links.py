from datetime import datetime

from sqlalchemy import insert, or_, select, update

from url_shortener.models import Link
from url_shortener.repositories.base import BaseRepository


class LinkRepository(BaseRepository[Link]):
    model = Link

    async def add(
        self,
        user_id: int,
        original_url: str,
        short_code: str,
        expires_at: datetime | None = None,
    ) -> Link:
        stmt = (
            insert(self.model)
            .values(
                user_id=user_id,
                original_url=original_url,
                short_code=short_code,
                expires_at=expires_at,
            )
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_code(
        self, 
        code: str
    ) -> Link | None:
        query = (
            select(self.model).
            where(self.model.short_code == code)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def increment_clicks_if_active(
        self,
        code: str,
        now: datetime,
    ) -> Link | None:
        stmt = (
            update(self.model)
            .where(
                self.model.short_code == code,
                self.model.is_active.is_(True),
                or_(
                    self.model.expires_at.is_(None),
                    self.model.expires_at > now,
                ),
            )
            .values(clicks_count=self.model.clicks_count + 1)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int) -> list[Link]:
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.user_id.desc())
        )
        models = await self.session.execute(query)
        return list(models.scalars().all())
