from url_shortener.repositories import LinkRepository
from url_shortener.schemas import LinkResponse
from url_shortener.utils.code_generator import generate_short_code


class LinkService:
    def __init__(self, repository: LinkRepository):
        self.repo = repository 

    async def create_link(self, original_url: str) -> LinkResponse:
        for _ in range(5):
            short_code = generate_short_code()
            test_code_collision = await self.repo.get_by_code(short_code)
            if not test_code_collision:
                break
        
        
        model = await self.repo.add(original_url, short_code)
        await self.repo.commit()
        return LinkResponse.model_validate(model)

    async def get_by_code(self, code: str) -> LinkResponse | None:
        model = await self.repo.get_by_code(code)
        if model:
            return LinkResponse.model_validate(model)
        return None