import uuid

from locust import HttpUser, between, task


class UrlShortenerUser(HttpUser):
    wait_time = between(0.5, 1.5)
    short_code = None

    def on_start(self):
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        password = "strongpassword123"

        self.client.post(
            "/api/v1/auth/register", json={"email": email, "password": password}
        )

        login_resp = self.client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        token = login_resp.json().get("access_token")

        if token:
            headers = {"Authorization": f"Bearer {token}"}
            link_resp = self.client.post(
                "/api/v1/links",
                json={"url": "https://example.com/load-test"},
                headers=headers,
            )
            self.short_code = link_resp.json().get("short_code")

    @task
    def get_redirect(self):
        if self.short_code:
            self.client.get(
                f"/{self.short_code}", allow_redirects=False, name="/{code}"
            )
