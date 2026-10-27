from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from url_shortener.utils.code_generator import generate_short_code


async def create_link(
    authorized_client: AsyncClient, url: str, expires_at: str | None = None
):
    return await authorized_client.post(
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


async def test_create_and_get_link(authorized_client: AsyncClient) -> None:
    create_resp = await create_link(authorized_client, url="https://example.com/some")
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["original_url"] == "https://example.com/some"
    assert data["clicks_count"] == 0
    assert data["is_active"] is True
    code = data["short_code"]

    get_resp = await authorized_client.get(f"/api/v1/links/{code}")
    assert get_resp.status_code == 200
    assert get_resp.json()["short_code"] == code


async def test_create_link_past_expiration_fails(
    authorized_client: AsyncClient,
) -> None:
    past_date = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    response = await create_link(
        authorized_client, url="https://example.com", expires_at=past_date
    )
    assert response.status_code == 422


async def test_redirect_increments_clicks(authorized_client: AsyncClient) -> None:
    create_resp = await create_link(authorized_client, url="https://example.com/target")
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


async def test_get_all_by_user(authorized_client: AsyncClient) -> None:
    await create_link(authorized_client, url="https://example.com/1")
    await create_link(authorized_client, url="https://example.com/2")

    get_resp = await authorized_client.get("/api/v1/links")

    assert get_resp.status_code == 200

    get_data = get_resp.json()
    assert len(get_data) == 2
    assert get_data[0]["original_url"] == "https://example.com/2"
    assert get_data[1]["original_url"] == "https://example.com/1"


async def test_delete_user_link(authorized_client: AsyncClient) -> None:
    create_resp = await create_link(authorized_client, url="https://example.com")
    assert create_resp.status_code == 201

    link_data = create_resp.json()
    link_id = link_data["id"]
    short_code = link_data["short_code"]

    delete_resp = await authorized_client.delete(f"/api/v1/links/{link_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["id"] == link_id

    get_resp = await authorized_client.get(f"/api/v1/links/{short_code}")
    assert get_resp.status_code == 404


async def test_deactivate_and_activate_user_link(
    authorized_client: AsyncClient,
) -> None:
    create_resp = await create_link(authorized_client, url="https://example.com")
    assert create_resp.status_code == 201

    link_data = create_resp.json()
    link_id = link_data["id"]
    short_code = link_data["short_code"]
    assert create_resp.json()["is_active"] is True

    deactivate_resp = await authorized_client.patch(
        f"/api/v1/links/{link_id}/deactivate"
    )

    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["is_active"] is False

    redirect_resp = await authorized_client.get(f"/{short_code}")
    assert redirect_resp.status_code == 404

    activate_resp = await authorized_client.patch(f"/api/v1/links/{link_id}/activate")
    assert activate_resp.status_code == 200
    assert activate_resp.json()["is_active"] is True
