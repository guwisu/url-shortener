# url-shortener [](https://www.python.org/) [](https://opensource.org/licenses/MIT)

An asynchronous REST API service for shortening URLs. The service provides user authentication, link management, expiration controls, click tracking, and fast redirects using Redis caching.

## Features

* User registration and JWT-based authentication
* Create, manage, deactivate, and delete shortened URLs
* Custom link expiration dates
* Fast HTTP 307 redirects with Redis caching
* Click tracking and statistics
* Custom exception handling and domain errors
* Database migrations support
* Containerized environment with Docker
* Automated testing with Pytest
* CI pipeline via GitHub Actions

## Tech Stack

* Python 3.13
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Redis
* Pydantic
* Pytest
* Docker / Docker Compose
* GitHub Actions
* uv

## Project Structure

```
url-shortener/
├── .github/
│   └── workflows/
├── migrations/
├── src/
│   └── url_shortener/
│       ├── api/
│       ├── core/
│       ├── db/
│       ├── models/
│       ├── repositories/
│       ├── schemas/
│       ├── services/
│       └── utils/
└──tests/
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/guwisu/url-shortener.git
cd url-shortener

```

2. Copy environment variables file:

```bash
cp .env.example .env

```

3. Build and start containers with Docker:

```bash
docker compose up -d --build

```

4. Access the API documentation:

```bash
http://localhost:8000/docs

```

## Testing

1. Start test databases (PostgreSQL and Redis):

```bash
docker compose -f docker-compose.test.yml up -d

```

2. Run the test suite:

```bash
uv run pytest -v

```

## License

This project is under the MIT license.
