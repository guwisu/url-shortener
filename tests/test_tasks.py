import asyncio
import socket
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener.models import Link
from url_shortener.tasks.emails import send_welcome_email_task
from url_shortener.tasks.maintenance import (
    _check_url_is_alive_batch,
    _deactivate_expired_links_async,
)
from url_shortener.tasks.sync import sync_clicks_to_db
from url_shortener.utils.security import check_url_is_alive


async def test_sync_clicks_to_db(db_session: AsyncSession, redis_client: Redis, user_1):
    short_code = "task123"
    link = Link(
        original_url="https://example.com",
        short_code=short_code,
        user_id=user_1.id,
        clicks_count=0,
    )
    db_session.add(link)
    await db_session.commit()

    await redis_client.set(f"clicks:{short_code}", "5")

    await sync_clicks_to_db(redis_client, db_session)

    await db_session.refresh(link)
    assert link.clicks_count == 5

    redis_clicks = await redis_client.get(f"clicks:{short_code}")
    assert redis_clicks is None


@pytest.mark.asyncio
async def test_deactivate_expired_links(db_session: AsyncSession, user_1, monkeypatch):
    expired_link = Link(
        original_url="https://expired.com",
        short_code="exp_link",
        user_id=user_1.id,
        is_active=True,
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    valid_link = Link(
        original_url="https://valid.com",
        short_code="val_link",
        user_id=user_1.id,
        is_active=True,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    db_session.add_all([expired_link, valid_link])
    await db_session.commit()

    await _deactivate_expired_links_async()

    db_session.expire_all()

    exp_db = await db_session.scalar(
        select(Link).where(Link.original_url == "https://expired.com")
    )
    val_db = await db_session.scalar(
        select(Link).where(Link.original_url == "https://valid.com")
    )

    assert exp_db is not None
    assert val_db is not None

    assert exp_db.is_active is False
    assert val_db.is_active is True


def test_send_welcome_email_task():

    with patch(
        "url_shortener.tasks.emails._send_welcome_email_async", new_callable=AsyncMock
    ) as mock_send:
        result = send_welcome_email_task.apply(args=["test@example.com"])  # type: ignore[attr-defined]

        assert result.status == "SUCCESS"

        mock_send.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_check_url_is_alive_logic(httpx_mock, fake_dns):
    sem = asyncio.Semaphore(1)
    async with httpx.AsyncClient() as client:
        httpx_mock.add_response(
            url="https://google.com", method="HEAD", status_code=200
        )
        assert await check_url_is_alive("https://google.com", sem, client) is True

        httpx_mock.add_response(
            url="https://google.com/error", method="HEAD", status_code=500
        )
        assert (
            await check_url_is_alive("https://google.com/error", sem, client) is False
        )

        httpx_mock.add_response(
            url="https://google.com/fallback", method="HEAD", status_code=405
        )
        httpx_mock.add_response(
            url="https://google.com/fallback", method="GET", status_code=200
        )
        assert (
            await check_url_is_alive("https://google.com/fallback", sem, client) is True
        )


@pytest.mark.asyncio
async def test_check_url_is_alive_blocks_private_ip(httpx_mock, monkeypatch):
    async def fake_getaddrinfo(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]

    monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", fake_getaddrinfo)
    async with httpx.AsyncClient() as client:
        assert (
            await check_url_is_alive("https://evil.com", asyncio.Semaphore(1), client)
            is False
        )
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_dead_link_revives(db_session: AsyncSession, user_1, monkeypatch):
    link = Link(
        original_url="https://back.com",
        short_code="back11",
        user_id=user_1.id,
        is_alive=False,
    )
    db_session.add(link)
    await db_session.commit()

    async def fake_check(url, semaphore, client):
        return True

    monkeypatch.setattr(
        "url_shortener.tasks.maintenance.check_url_is_alive", fake_check
    )

    await _check_url_is_alive_batch()
    await db_session.refresh(link)

    assert link.is_alive is True
    assert link.last_checked_at is not None
