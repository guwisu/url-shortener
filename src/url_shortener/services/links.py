from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from url_shortener.repositories import LinkRepository
from url_shortener.schemas import LinkResponse
from url_shortener.utils.code_generator import generate_short_code


class LinkService:
    def __init__(self, repository: LinkRepository):
        self.repo = repository

    async def create_link(
        self, user_id: int, original_url: str, expires_at: datetime | None
    ) -> LinkResponse:
        for _ in range(5):
            short_code = generate_short_code()
            try:
                model = await self.repo.add(
                    user_id, original_url, short_code, expires_at
                )
                await self.repo.commit()
                return LinkResponse.model_validate(model)
            except IntegrityError:
                await self.repo.rollback()
                continue

        raise HTTPException(
            status_code=503, detail="Service temporarily unavailable. Please try again."
        )

    async def get_by_code(self, code: str) -> LinkResponse | None:
        model = await self.repo.get_by_code(code)
        if model:
            return LinkResponse.model_validate(model)
        return None

    async def get_and_increment_clicks(self, code: str) -> LinkResponse:
        model = await self.repo.get_by_code(code)
        if not model:
            raise HTTPException(status_code=404, detail="Link not found")

        now = datetime.now(UTC)
        if not model.is_active or (model.expires_at and model.expires_at < now):
            raise HTTPException(
                status_code=410, detail="Link has been expired or been deactivated"
            )

        updated_model = await self.repo.increment_clicks_if_active(code, now=now)
        await self.repo.commit()
        return LinkResponse.model_validate(updated_model)

    async def get_all_by_user(self, user_id: int) -> list[LinkResponse]:
        links = await self.repo.get_all_by_user(user_id)
        return list(map(LinkResponse.model_validate, links))

    async def delete_user_link(self, user_id: int, link_id: int) -> LinkResponse:
        result = await self.repo.delete_user_link(user_id, link_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Link not found")
        await self.repo.commit()
        return LinkResponse.model_validate(result)

    async def deactivate_user_link(self, user_id: int, link_id: int) -> LinkResponse:
        result = await self.repo.deactivate_user_link(user_id, link_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Link not found")
        await self.repo.commit()
        return LinkResponse.model_validate(result)

    async def activate_user_link(self, user_id: int, link_id: int) -> LinkResponse:
        result = await self.repo.activate_user_link(user_id, link_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Link not found")
        await self.repo.commit()
        return LinkResponse.model_validate(result)
