from httpx import AsyncClient


async def register_user(client: AsyncClient):
    return await client.post(
        url="/api/v1/auth/register",
        json={"email": "new@example.com", "password": "test_password123"},
    )


async def login_user(client: AsyncClient, email: str, password: str):
    return await client.post(
        url="/api/v1/auth/login", json={"email": email, "password": password}
    )


async def test_register_success(client: AsyncClient):
    response = await register_user(client)
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 3
    assert data["email"] and data["id"] and data["created_at"]


async def test_register_duplicate(client: AsyncClient):
    await register_user(client)
    response2 = await register_user(client)

    assert response2.status_code == 400


async def test_login_success(client: AsyncClient):
    await register_user(client)

    login_response = await login_user(
        client, email="new@example.com", password="test_password123"
    )

    assert login_response.status_code == 200
    assert login_response.json()["access_token"]


async def test_login_wrong_password(client: AsyncClient):
    await register_user(client)

    login_wrong_password_response = await login_user(
        client, email="new@example.com", password="wrong_password"
    )
    assert login_wrong_password_response.status_code == 401
