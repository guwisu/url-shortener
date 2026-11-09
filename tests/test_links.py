import json
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener.models import Link
from url_shortener.utils.code_generator import generate_short_code


async def create_link(
    auth_client_1: AsyncClient, url: str, expires_at: str | None = None
):
    return await auth_client_1.post(
        "/api/v1/links",
        json={"url": url, "expires_at": expires_at},
    )


def test_generate_short_code() -> None:
    code = generate_short_code(length=6)
    assert len(code) == 6
    assert code.isalnum()


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


async def test_create_and_get_link(auth_client_1: AsyncClient) -> None:
    create_resp = await create_link(auth_client_1, url="https://example.com/some")
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["original_url"] == "https://example.com/some"
    assert data["clicks_count"] == 0
    assert data["is_active"] is True
    code = data["short_code"]

    get_resp = await auth_client_1.get(f"/api/v1/links/{code}")
    assert get_resp.status_code == 200
    assert get_resp.json()["short_code"] == code


async def test_create_link_past_expiration_fails(
    auth_client_1: AsyncClient,
) -> None:
    past_date = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    response = await create_link(
        auth_client_1, url="https://example.com", expires_at=past_date
    )
    assert response.status_code == 422


async def test_redirect_increments_clicks(auth_client_1: AsyncClient) -> None:
    create_resp = await create_link(auth_client_1, url="https://example.com/target")
    code = create_resp.json()["short_code"]

    redirect_resp = await auth_client_1.get(f"/{code}")
    assert redirect_resp.status_code == 307
    assert redirect_resp.headers["location"] == "https://example.com/target"

    info_resp = await auth_client_1.get(f"/api/v1/links/{code}")
    assert info_resp.json()["clicks_count"] == 1


async def test_not_found_link(client: AsyncClient, auth_client_1: AsyncClient) -> None:
    resp_info = await auth_client_1.get("/api/v1/links/nonexistent")
    assert resp_info.status_code == 404

    resp_redirect = await client.get("/nonexistent")
    assert resp_redirect.status_code == 404


async def test_get_all_by_user(auth_client_1: AsyncClient) -> None:
    await create_link(auth_client_1, url="https://example.com/1")
    await create_link(auth_client_1, url="https://example.com/2")

    get_resp = await auth_client_1.get("/api/v1/links")

    assert get_resp.status_code == 200

    get_data = get_resp.json()
    assert len(get_data) == 2
    assert get_data[0]["original_url"] == "https://example.com/2"
    assert get_data[1]["original_url"] == "https://example.com/1"

    get_paginated_resp = await auth_client_1.get("/api/v1/links?skip=1&limit=1")
    assert get_paginated_resp.status_code == 200

    paginated_data = get_paginated_resp.json()

    assert len(paginated_data) == 1

    assert paginated_data[0]["original_url"] == "https://example.com/1"


async def test_delete_user_link(auth_client_1: AsyncClient) -> None:
    create_resp = await create_link(auth_client_1, url="https://example.com")
    assert create_resp.status_code == 201

    link_data = create_resp.json()
    short_code = link_data["short_code"]

    delete_resp = await auth_client_1.delete(f"/api/v1/links/{short_code}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["short_code"] == short_code

    get_resp = await auth_client_1.get(f"/api/v1/links/{short_code}")
    assert get_resp.status_code == 404


async def test_deactivate_and_activate_user_link(
    auth_client_1: AsyncClient,
) -> None:
    create_resp = await create_link(auth_client_1, url="https://example.com")
    assert create_resp.status_code == 201

    link_data = create_resp.json()
    short_code = link_data["short_code"]
    assert create_resp.json()["is_active"] is True

    deactivate_resp = await auth_client_1.patch(f"/api/v1/links/{short_code}/deactivate")

    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["is_active"] is False

    redirect_resp = await auth_client_1.get(f"/{short_code}")
    assert redirect_resp.status_code == 410

    activate_resp = await auth_client_1.patch(f"/api/v1/links/{short_code}/activate")
    assert activate_resp.status_code == 200
    assert activate_resp.json()["is_active"] is True


async def test_change_someones_link(
    auth_client_1: AsyncClient, auth_client_2: AsyncClient
) -> None:
    create_resp = await create_link(auth_client_1, url="https://example.com")
    assert create_resp.status_code == 201

    link_data = create_resp.json()
    short_code = link_data["short_code"]

    delete_resp = await auth_client_2.delete(f"/api/v1/links/{short_code}")
    assert delete_resp.status_code == 404

    deactivate_resp = await auth_client_2.patch(f"/api/v1/links/{short_code}/deactivate")
    assert deactivate_resp.status_code == 404

    activate_resp = await auth_client_2.patch(f"/api/v1/links/{short_code}/activate")
    assert activate_resp.status_code == 404

    redirect_resp = await auth_client_2.get(f"/{short_code}")
    assert redirect_resp.status_code == 307


async def test_redirect_expired_link(
    db_session: AsyncSession, client: AsyncClient, user_1
) -> None:
    past_date = datetime.now(UTC) - timedelta(days=1)
    short_code = "abc123"

    link = Link(
        original_url="https://example.com",
        short_code=short_code,
        user_id=user_1.id,
        expires_at=past_date,
        is_active=True,
    )
    db_session.add(link)
    await db_session.commit()

    redirect_resp = await client.get(f"/{short_code}")
    assert redirect_resp.status_code == 410


async def test_non_authorized_client_requests(client: AsyncClient) -> None:
    create_resp = await create_link(
        client,
        url="https://example.com",
    )
    assert create_resp.status_code == 401

    get_resp = await client.get("/api/v1/links")
    assert get_resp.status_code == 401


async def test_redirect_uses_cache(client: AsyncClient, redis_client: Redis):

    short_code = "fake123"
    cache_key = f"link:{short_code}"
    fake_data = {
        "original_url": "https://cache-hit.com",
        "is_active": True,
    }

    await redis_client.set(cache_key, json.dumps(fake_data), ex=3600)

    redirect_resp = await client.get(f"/{short_code}")

    assert redirect_resp.status_code == 307
    assert redirect_resp.headers["location"] == "https://cache-hit.com"

    clicks = await redis_client.get(f"clicks:{short_code}")
    assert clicks is not None
    assert int(clicks) == 1


async def test_redirect_deactivated_in_cache(client: AsyncClient, redis_client: Redis):
    short_code = "dead123"

    await redis_client.set(
        f"link:{short_code}",
        json.dumps({"original_url": "https://example.com", "is_active": False}),
        ex=3600,
    )

    redirect_resp = await client.get(f"/{short_code}")
    assert redirect_resp.status_code == 410


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/x",
        "http://127.0.0.1",
        "http://192.168.1.1",
        "http://10.0.0.5",
        "http://169.254.169.254",
        "http://[::1]/",
    ],
)
async def test_create_link_private_url_fails(auth_client_1: AsyncClient, url: str):
    created_resp = await create_link(auth_client_1, url)
    assert created_resp.status_code == 422


async def test_link_rate_limit(auth_client_1, enabled_limiter):
    for _ in range(20):
        created_resp = await create_link(auth_client_1, "https://example.com")
        assert created_resp.status_code == 201

    created_resp = await create_link(auth_client_1, "https://example.com")
    assert created_resp.status_code == 429
