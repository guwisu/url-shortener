from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.collection import AsyncCollection

CLICK_EVENT_TTL_SECONDS = 90 * 24 * 60 * 60


async def ensure_click_events_indexes(collection: AsyncCollection) -> None:
    await collection.create_index(
        [("short_code", ASCENDING), ("timestamp", DESCENDING)],
        name="idx_short_code_timestamp",
    )

    await collection.create_index(
        [("timestamp", ASCENDING)],
        expireAfterSeconds=CLICK_EVENT_TTL_SECONDS,
        name="idx_timestamp_ttl",
    )
