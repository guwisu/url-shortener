from locust import HttpUser, between, task


class UrlShortenerUser(HttpUser):
    wait_time = between(0.5, 1.5)
    short_code =  "8lTvxn"

    @task
    def get_redirect(self):
        """Redirection by link is the most popular user feature"""
        if self.short_code:
            self.client.get(f"/{self.short_code}", allow_redirects=False, name="/{code}")