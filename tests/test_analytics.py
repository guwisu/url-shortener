from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

from httpx import AsyncClient
from pymongo.asynchronous.collection import AsyncCollection

from url_shortener.api.dependencies import get_event_publisher
from url_shortener.main import app
from url_shortener.schemas.analytics import ClickEvent
from url_shortener.services.events import EventPublisher
from url_shortener.tasks.consumer import write_click_events_batch


async def test_redirect_publishes_click_event(
    auth_client_1: AsyncClient, mock_event_publisher
) -> None:
    create_resp = await auth_client_1.post(
        "/api/v1/links", json={"url": "https://example.com/analytics"}
    )

    code = create_resp.json()["short_code"]

    resp = await auth_client_1.get(
        f"/{code}",
        headers={
            "referer": "https://google.com",
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
        },
    )
    assert resp.status_code == 307

    mock_event_publisher.publish_click.assert_awaited_once()

    event: ClickEvent = mock_event_publisher.publish_click.call_args[0][0]
    assert event.short_code == code
    assert event.referer == "https://google.com"
    assert event.ip_hash != "127.0.0.1"


async def test_redirect_survives_kafka_error(auth_client_1: AsyncClient) -> None:
    create_resp = await auth_client_1.post(
        "/api/v1/links", json={"url": "https://example.com/kafka-down"}
    )
    code = create_resp.json()["short_code"]

    failing_producer = AsyncMock()
    failing_producer.send.side_effect = RuntimeError("Kafka down")
    publisher = EventPublisher(producer=failing_producer, topic="clicks")
    app.dependency_overrides[get_event_publisher] = lambda: publisher

    resp = await auth_client_1.get(f"/{code}")
    assert resp.status_code == 307
    failing_producer.send.assert_awaited_once()


async def test_consumer_batch_is_idempotent(
    mongo_collection: AsyncCollection[dict[str, Any]],
) -> None:
    event_1 = ClickEvent(
        event_id=uuid4(),
        short_code="abc123",
        timestamp=datetime(2026, 11, 20, 12, 0, tzinfo=UTC),
        ip_hash="hash1",
        referer="https://t.me",
        user_agent="curl/8.0",
    )
    event_2 = ClickEvent(
        event_id=uuid4(),
        short_code="abc123",
        timestamp=datetime(2026, 11, 20, 13, 0, tzinfo=UTC),
        ip_hash="hash2",
    )
    batch = [
        event_1.model_dump_json().encode("utf-8"),
        event_2.model_dump_json().encode("utf-8"),
    ]

    await write_click_events_batch(batch, mongo_collection)
    await write_click_events_batch(batch, mongo_collection)

    count = await mongo_collection.count_documents({"short_code": "abc123"})
    assert count == 2

    doc = await mongo_collection.find_one({"_id": str(event_1.event_id)})
    assert doc is not None
    assert isinstance(doc["timestamp"], datetime)


async def test_link_stats_aggregation_and_access(
    auth_client_1: AsyncClient,
    auth_client_2: AsyncClient,
    mongo_collection: AsyncCollection[dict[str, Any]],
) -> None:
    create_resp = await auth_client_1.post(
        "/api/v1/links", json={"url": "https://example.com/stats"}
    )
    code = create_resp.json()["short_code"]

    day_1 = datetime(2026, 11, 18, 10, 0, tzinfo=UTC)
    day_2 = datetime(2026, 11, 19, 15, 0, tzinfo=UTC)
    await mongo_collection.insert_many(
        [
            {
                "_id": str(uuid4()),
                "short_code": code,
                "timestamp": day_1,
                "ip_hash": "h1",
                "referer": "https://google.com",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0)",
            },
            {
                "_id": str(uuid4()),
                "short_code": code,
                "timestamp": day_2,
                "ip_hash": "h2",
                "referer": None,
                "user_agent": "Mozilla/5.0 (iPhone)",
            },
            {
                "_id": str(uuid4()),
                "short_code": code,
                "timestamp": day_2 + timedelta(hours=1),
                "ip_hash": "h3",
                "referer": "https://google.com",
                "user_agent": "curl/8.0",
            },
        ]
    )

    resp = await auth_client_1.get(f"/api/v1/links/{code}/stats")
    assert resp.status_code == 200

    data = resp.json()

    assert data["total_clicks"] == 3
    assert data["by_day"] == [
        {"date": "2026-11-18", "clicks": 1},
        {"date": "2026-11-19", "clicks": 2},
    ]
    assert data["top_referers"][0] == {"referer": "https://google.com", "clicks": 2}
    assert {d["device"]: d["clicks"] for d in data["devices"]} == {
        "desktop": 1,
        "mobile": 1,
        "bot": 1,
    }

    filtered = await auth_client_1.get(
        f"/api/v1/links/{code}/stats",
        params={"from": "2026-11-19T00:00:00Z"},
    )
    assert filtered.status_code == 200
    assert filtered.json()["total_clicks"] == 2

    forbidden = await auth_client_2.get(f"/api/v1/links/{code}/stats")
    assert forbidden.status_code == 404
