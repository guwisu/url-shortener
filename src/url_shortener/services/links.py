from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from url_shortener.core.config import settings
from url_shortener.core.exceptions import (
    LinkDeactivated,
    LinkNotFound,
    ServiceUnavailable,
)
from url_shortener.repositories import LinkRepository
from url_shortener.schemas import LinkResponse
from url_shortener.schemas.links import RedirectTarget
from url_shortener.services.cache import LinkCache
from url_shortener.utils.code_generator import generate_short_code


class LinkService:
    def __init__(self, repository: LinkRepository, cache: LinkCache):
        self.repo = repository
        self.cache = cache

    async def create_link(
        self, user_id: int, original_url: str, expires_at: datetime | None
    ) -> LinkResponse:
        for _ in range(5):
            short_code = generate_short_code()
            if short_code in settings.SYSTEM_WORDS:
                continue
            try:
                model = await self.repo.add(
                    user_id, original_url, short_code, expires_at
                )
                await self.repo.commit()
                return LinkResponse.model_validate(model)
            except IntegrityError as e:
                await self.repo.rollback()
                if "short_code" in str(e.orig):
                    continue
                raise

        raise ServiceUnavailable

    async def get_by_code(self, user_id: int, code: str) -> LinkResponse | None:
        link = await self.repo.get_by_code(user_id, code)
        if not link:
            raise LinkNotFound
        response = LinkResponse.model_validate(link)
        redis_clicks = await self.cache.get_clicks(code)
        response.clicks_count += redis_clicks
        return response

    async def redirect_by_code(self, code: str) -> RedirectTarget:
        cached_link = await self.cache.get(code)
        if cached_link:
            if cached_link.get("not_found") is True:
                raise LinkNotFound

            if not cached_link["is_active"]:
                raise LinkDeactivated
            else:
                await self.cache.increment_clicks(code)
                return RedirectTarget(original_url=cached_link["original_url"])

        model = await self.repo.redirect_by_code(code)

        if not model:
            await self.cache.set(code, {"not_found": True}, 30)
            raise LinkNotFound

        now = datetime.now(UTC)
        is_alive = model.is_active and (
            model.expires_at is None or model.expires_at > now
        )

        if not is_alive:
            await self.cache.set(model.short_code, {"is_active": False}, 60)
            raise LinkDeactivated

        if model.expires_at is None:
            time_to_expire = 3600
        else:
            time_left = int((model.expires_at - now).total_seconds())
            time_to_expire = max(1, min(time_left, 3600))

        link_data = {"original_url": model.original_url, "is_active": True}
        await self.cache.set(model.short_code, link_data, time_to_expire)

        await self.cache.increment_clicks(code)
        return RedirectTarget(original_url=model.original_url)

    async def get_all_by_user(
        self, user_id: int, skip: int, limit: int
    ) -> list[LinkResponse]:
        links = await self.repo.get_all_by_user(user_id, skip, limit)
        return list(map(LinkResponse.model_validate, links))

    async def delete_user_link(self, user_id: int, code: str) -> LinkResponse:
        result = await self.repo.delete_user_link(user_id, code)
        if result is None:
            raise LinkNotFound
        await self.repo.commit()

        await self.cache.delete(result.short_code)

        return LinkResponse.model_validate(result)

    async def set_active(self, user_id: int, code: str, value: bool) -> LinkResponse:
        result = await self.repo.set_active(user_id, code, value)
        if result is None:
            raise LinkNotFound
        await self.repo.commit()

        await self.cache.delete(result.short_code)

        return LinkResponse.model_validate(result)
