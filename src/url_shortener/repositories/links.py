from datetime import datetime

from sqlalchemy import delete, insert, select, update

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

    async def get_by_code(self, user_id: int, code: str) -> Link | None:
        query = select(self.model).where(
            self.model.short_code == code,
            self.model.user_id == user_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def redirect_by_code(self, code: str) -> Link | None:
        query = select(self.model).where(self.model.short_code == code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int, skip: int, limit: int = 100) -> list[Link]:
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        models = await self.session.execute(query)
        return list(models.scalars().all())

    async def delete_user_link(self, user_id: int, link_id: int) -> Link | None:
        stmt = (
            delete(self.model)
            .where(self.model.user_id == user_id, self.model.id == link_id)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate_user_link(self, user_id: int, link_id: int) -> Link | None:
        stmt = (
            update(self.model)
            .values(
                is_active=False,
            )
            .where(self.model.user_id == user_id, self.model.id == link_id)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def activate_user_link(self, user_id: int, link_id: int) -> Link | None:
        stmt = (
            update(self.model)
            .values(
                is_active=True,
            )
            .where(self.model.user_id == user_id, self.model.id == link_id)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
