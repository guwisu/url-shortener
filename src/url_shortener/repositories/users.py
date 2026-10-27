from sqlalchemy import insert, select

from url_shortener.models import User
from url_shortener.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def add(self, email: str, hashed_password: str) -> User:
        stmt = (
            insert(self.model)
            .values(email=email, hashed_password=hashed_password)
            .returning(self.model)
        )
        model = await self.session.execute(stmt)
        return model.scalar_one()

    async def get_by_id(self, user_id: int) -> User | None:
        query = select(self.model).where(self.model.id == user_id)
        model = await self.session.execute(query)
        return model.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        query = select(self.model).where(self.model.email == email)
        model = await self.session.execute(query)
        return model.scalar_one_or_none()
