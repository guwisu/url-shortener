from typing import Annotated

from fastapi import APIRouter, Depends, status

from url_shortener.api.dependencies import get_auth_service
from url_shortener.schemas import TokenResponse, UserCreate, UserResponse
from url_shortener.services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    service: Annotated[AuthService, Depends(get_auth_service)]
) -> UserResponse:
    return await service.register(body.email, body.password)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserCreate,
    service: Annotated[AuthService, Depends(get_auth_service)]
) -> TokenResponse:
    return await service.login(body.email, body.password)