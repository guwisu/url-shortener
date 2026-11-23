import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from typing import Any

from aiokafka import AIOKafkaConsumer
from pymongo import AsyncMongoClient, UpdateOne
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import BulkWriteError, PyMongoError

from url_shortener.core.config import settings
from url_shortener.db.mongo import ensure_click_events_indexes

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


async def process_messages(stop_event: asyncio.Event):
    consumer = AIOKafkaConsumer(
        settings.KAFKA_CLICK_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="analytics_group",
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )

    mongo_client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        settings.mongo_url
    )
    db = mongo_client[settings.MONGO_DB]
    collection = db["click_events"]

    await ensure_click_events_indexes(collection)

    await consumer.start()
    log.info("Kafka Consumer started, listening for clicks...")

    try:
        while not stop_event.is_set():
            result = await consumer.getmany(timeout_ms=1000, max_records=100)
            if not result:
                continue

            raw_messages = [
                msg.value
                for messages in result.values()
                for msg in messages
                if msg.value is not None
            ]

            if raw_messages:
                try:
                    written = await write_click_events_batch(raw_messages, collection)
                    if written:
                        await consumer.commit()
                        log.info(
                            f"Successfully processed and committed {written} events"
                        )
                except BulkWriteError as bwe:
                    log.error(f"MongoDB bulk write error: {bwe.details}")
                except PyMongoError as e:
                    log.error(f"Failed to write to MongoDB: {e}")
    finally:
        log.info("Shutting down Consumer...")
        await consumer.stop()
        await mongo_client.close()


async def main():
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    if sys.platform != "win32":
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, stop_event.set)
    try:
        await process_messages(stop_event)
    except KeyboardInterrupt:
        log.info("Received KeyboardInterrupt (Windows)")
        stop_event.set()


async def write_click_events_batch(
    raw_messages: list[bytes],
    collection: AsyncCollection[dict[str, Any]],
) -> int:
    operations: list[UpdateOne] = []

    for raw in raw_messages:
        try:
            data = json.loads(raw.decode("utf-8"))
            doc_id = data.pop("event_id")
            data["_id"] = doc_id
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

            operations.append(
                UpdateOne({"_id": doc_id}, {"$setOnInsert": data}, upsert=True)
            )
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            KeyError,
            ValueError,
            TypeError,
        ) as e:
            log.error(f"Failed to parse message: {e}")

    if not operations:
        return 0

    await collection.bulk_write(operations, ordered=False)
    return len(operations)


if __name__ == "__main__":
    asyncio.run(main())
