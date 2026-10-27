from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from url_shortener.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from url_shortener.repositories import UserRepository
from url_shortener.schemas import TokenResponse, UserResponse


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repo = repository

    async def register(self, email: str, password: str) -> UserResponse:
        lower_email = email.lower()
        test_user = await self.repo.get_by_email(lower_email)
        if test_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = hash_password(password)
        try:
            user = await self.repo.add(lower_email, hashed_password)
            await self.repo.commit()
            return UserResponse.model_validate(user)
        except IntegrityError:
            await self.repo.rollback()
            raise HTTPException(status_code=400, detail="Email already registered")

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.repo.get_by_email(email)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(user.id)
        return TokenResponse(access_token=token)
