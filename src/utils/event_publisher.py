import json
import logging

from google.cloud import pubsub_v1

from src.application.interfaces.event_publisher import AbstractEventPublisher
from src.application import events


class EventPublisher(AbstractEventPublisher):
    def __init__(
        self,
        project_id: str,
    ):
        self.publisher = self._build_publisher()
        self.project_id = project_id

    def __getstate__(self):
        return {"project_id": self.project_id}

    def __setstate__(self, state):
        self.project_id = state["project_id"]
        self.publisher = self._build_publisher()

    @staticmethod
    def _build_publisher() -> pubsub_v1.PublisherClient:
        # credential = credentials.Credentials.from_authorized_user_file(
        #     filename, scopes=["https://www.googleapis.com/auth/pubsub"]
        # )
        return pubsub_v1.PublisherClient()  # credential=credential)

    def _registration(self, event: events.Event, topic: str, **kwargs) -> str:
        try:
            topic_path = self.publisher.topic_path(self.project_id, topic)
            encode_event_event = json.dumps(event.to_dict(), indent=2).encode("utf-8")
            logging.info(f"publish - {encode_event_event}")
            res = self.publisher.publish(topic=topic_path, data=encode_event_event, **kwargs)
            id = res.result(timeout=30)
            return id
        except Exception as exc:
            logging.error(f"Error registration event: {exc}")