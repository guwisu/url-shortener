from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from url_shortener.repositories import LinkRepository
from url_shortener.schemas import LinkResponse
from url_shortener.utils.code_generator import generate_short_code


class LinkService:
    def __init__(self, repository: LinkRepository):
        self.repo = repository 

    async def create_link(self, original_url: str, expired_at: datetime | None) -> LinkResponse:
        for _ in range(5):
            short_code = generate_short_code()
            try:
                model = await self.repo.add(original_url, short_code, expired_at)
                await self.repo.commit()
                return LinkResponse.model_validate(model)
            except IntegrityError:
                await self.repo.rollback()
                continue
                
        raise RuntimeError("Could not generate unique short code")

    async def get_by_code(self, code: str) -> LinkResponse | None:
        model = await self.repo.get_by_code(code)
        if model:
            return LinkResponse.model_validate(model)
        return None

    async def get_and_increment_clicks(self, code: str) -> LinkResponse | None:
        model = await self.repo.get_by_code(code)    
        if model and model.is_active and (model.expires_at is None or model.expires_at > datetime.now(UTC)):
            await self.repo.increment_clicks(code)
            await self.repo.commit()
            return LinkResponse.model_validate(model)
        return None   
