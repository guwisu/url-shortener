from url_shortener.repositories.users import UserRepository


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repo = repository
