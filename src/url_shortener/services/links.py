from url_shortener.repositories import LinkRepository
from url_shortener.schemas import LinkResponse
from url_shortener.utils.code_generator import generate_short_code


class LinkService:
    def __init__(self, session):
        self.db = LinkRepository(session)

    async def create_link(self, original_url: str) -> LinkResponse:
        short_code = generate_short_code()
        model = await self.db.add(original_url, short_code)
        await self.db.session.commit()
        return LinkResponse.model_validate(model)

    async def get_by_code(self, code: str) -> LinkResponse | None:
        model = await self.db.get_by_code(code)
        if model:
            return LinkResponse.model_validate(model)
        return None