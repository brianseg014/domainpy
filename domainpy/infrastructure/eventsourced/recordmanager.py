from datetime import datetime

from domainpy.infrastructure.records import EventRecord


class EventRecordManager:
    def session(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} must override session method"
        )  # pragma: no cover

    def get_records(
        self,
        stream_id: str,
        topic: str = None,
        from_timestamp: datetime = None,
        to_timestamp: datetime = None,
        from_number: int = None,
        to_number: int = None,
    ) -> tuple[EventRecord]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must override find method"
        )  # pragma: no cover


class Session:
    def append(self, event_record):
        raise NotImplementedError(
            f"{self.__class__.__name__} must override append method"
        )  # pragma: no cover
