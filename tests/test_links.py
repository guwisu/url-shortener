from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from url_shortener.utils.code_generator import generate_short_code


def test_generate_short_code() -> None:
    code = generate_short_code(length=6)
    assert len(code) == 6
    assert code.isalnum()


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


async def test_create_and_get_link(authorized_client: AsyncClient) -> None:
    create_resp = await authorized_client.post(
        "/api/v1/links",
        json={"url": "https://example.com/some/path"},
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["original_url"] == "https://example.com/some/path"
    assert data["clicks_count"] == 0
    assert data["is_active"] is True
    code = data["short_code"]

    get_resp = await authorized_client.get(f"/api/v1/links/{code}")
    assert get_resp.status_code == 200
    assert get_resp.json()["short_code"] == code


async def test_create_link_past_expiration_fails(authorized_client: AsyncClient) -> None:
    past_date = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    response = await authorized_client.post(
        "/api/v1/links",
        json={"url": "https://example.com", "expires_at": past_date},
    )
    assert response.status_code == 422


async def test_redirect_increments_clicks(authorized_client: AsyncClient) -> None:
    create_resp = await authorized_client.post(
        "/api/v1/links",
        json={"url": "https://example.com/target"},
    )
    code = create_resp.json()["short_code"]

    redirect_resp = await authorized_client.get(f"/{code}")
    assert redirect_resp.status_code == 307
    assert redirect_resp.headers["location"] == "https://example.com/target"

    info_resp = await authorized_client.get(f"/api/v1/links/{code}")
    assert info_resp.json()["clicks_count"] == 1


async def test_not_found_link(client: AsyncClient) -> None:
    resp_info = await client.get("/api/v1/links/nonexistent")
    assert resp_info.status_code == 404

    resp_redirect = await client.get("/nonexistent")
    assert resp_redirect.status_code == 404

