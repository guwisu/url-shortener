from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from url_shortener.api.dependencies import get_auth_service
from url_shortener.core.rate_limit import limiter
from url_shortener.schemas import TokenResponse, UserCreate, UserResponse
from url_shortener.schemas.users import UserLogin
from url_shortener.services import AuthService
from url_shortener.tasks.emails import send_welcome_email_task

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: UserCreate,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    user = await service.register(body.email, body.password)
    send_welcome_email_task.delay(user.email)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: UserLogin,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return await service.login(body.email, body.password)
