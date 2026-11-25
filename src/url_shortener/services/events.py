import logging

from aiokafka import AIOKafkaProducer

from url_shortener.schemas.analytics import ClickEvent

log = logging.getLogger(__name__)


class EventPublisher:
    def __init__(self, producer: AIOKafkaProducer, topic: str):
        self.producer = producer
        self.topic = topic

    async def publish_click(self, event: ClickEvent) -> None:
        try:
            payload = event.model_dump_json().encode()

            key = event.short_code.encode()

            await self.producer.send(topic=self.topic, key=key, value=payload)
        except Exception as e:  # noqa: BLE001
            log.error(f"Failed to publish click event to Kafka: {e}")
