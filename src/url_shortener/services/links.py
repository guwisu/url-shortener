from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from url_shortener.repositories import LinkRepository
from url_shortener.schemas import LinkResponse
from url_shortener.schemas.links import RedirectResponse
from url_shortener.services import LinkCache
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

    async def get_by_code(self, code: str, cache: LinkCache) -> LinkResponse | None:
        model = await self.repo.get_by_code(code)
        if model:
            redis_clicks = await cache.get_clicks(code)
            model.clicks_count += redis_clicks
            return LinkResponse.model_validate(model)
        return None

    async def redirect_by_code(self, code: str, cache: LinkCache) -> RedirectResponse:
        cached_link = await cache.get(code)
        if cached_link:
            if cached_link.get("not_found") is True:
                raise HTTPException(status_code=404, detail="Link not found")

            if not cached_link["is_active"]:
                raise HTTPException(
                    status_code=410, detail="Link has been expired or been deactivated"
                )
            else:
                await cache.increment_clicks(code)
                return RedirectResponse(original_url=cached_link["original_url"])

        model = await self.repo.get_by_code(code)

        if not model:
            await cache.set(code, {"not_found": True}, 30)
            raise HTTPException(status_code=404, detail="Link not found")

        now = datetime.now(UTC)
        is_alive = model.is_active and (
            model.expires_at is None or model.expires_at > now
        )

        if not is_alive:
            await cache.set(model.short_code, {"is_active": False}, 60)
            raise HTTPException(
                status_code=410, detail="Link has been expired or been deactivated"
            )

        if model.expires_at is None:
            time_to_expire = 3600
        else:
            time_left = int((model.expires_at - datetime.now(UTC)).total_seconds())
            time_to_expire = max(1, min(time_left, 3600))

        link_data = {"original_url": model.original_url, "is_active": True}
        await cache.set(model.short_code, link_data, time_to_expire)

        await cache.increment_clicks(code)
        return RedirectResponse(original_url=model.original_url)

    async def get_all_by_user(self, user_id: int) -> list[LinkResponse]:
        links = await self.repo.get_all_by_user(user_id)
        return list(map(LinkResponse.model_validate, links))

    async def delete_user_link(
        self, user_id: int, link_id: int, cache: LinkCache
    ) -> LinkResponse:
        result = await self.repo.delete_user_link(user_id, link_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Link not found")
        await self.repo.commit()

        await cache.delete(result.short_code)

        return LinkResponse.model_validate(result)

    async def deactivate_user_link(
        self, user_id: int, link_id: int, cache: LinkCache
    ) -> LinkResponse:
        result = await self.repo.deactivate_user_link(user_id, link_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Link not found")
        await self.repo.commit()

        await cache.delete(result.short_code)

        return LinkResponse.model_validate(result)

    async def activate_user_link(
        self, user_id: int, link_id: int, cache: LinkCache
    ) -> LinkResponse:
        result = await self.repo.activate_user_link(user_id, link_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Link not found")
        await self.repo.commit()

        await cache.delete(result.short_code)

        return LinkResponse.model_validate(result)
