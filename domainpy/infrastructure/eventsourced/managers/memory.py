from datetime import datetime

from domainpy import exceptions as excs
from domainpy.infrastructure.eventsourced.recordmanager import (
    EventRecordManager,
    Session,
)
from domainpy.infrastructure.records import EventRecord


class MemoryEventRecordManager(EventRecordManager):
    def __init__(self, *args, **kwargs):
        self.heap: list[EventRecord] = []

    def session(self):
        return MemorySession(self)

    def get_records(
        self,
        stream_id: str,
        *,
        topic: str = None,
        from_timestamp: datetime = None,
        to_timestamp: datetime = None,
        from_number: int = None,
        to_number: int = None,
    ) -> tuple[EventRecord, ...]:

        filters = [lambda er: er.stream_id == stream_id]

        if topic is not None:
            filters.append(lambda er: er.topic == topic)

        if from_timestamp is not None:
            filters.append(lambda er: er.timestamp >= from_timestamp)

        if to_timestamp is not None:
            filters.append(lambda er: er.timestamp <= to_timestamp)

        if from_number is not None:
            filters.append(lambda er: er.number >= from_number)

        if to_number is not None:
            filters.append(lambda er: er.number <= to_number)

        return tuple([er for er in self.heap if all(f(er) for f in filters)])

    def clear(self):
        self.heap = []


class MemorySession(Session):
    def __init__(self, record_manager):
        self.record_manager = record_manager

        self.heap = []

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.rollback()

    def append(self, event_record: EventRecord):
        if event_record is None:
            raise TypeError("event_record cannot be none")

        self.heap.append(event_record)

    def commit(self):
        try:
            self._check_heap_merge()

            self.record_manager.heap.extend(self.heap)

        except UniqueEventRecordBroken as e:
            raise excs.ConcurrencyError() from e
        finally:
            self.heap = []

    def rollback(self):
        self.heap = []

    def _check_heap_merge(self):
        for e in self.heap:
            if self._check_if_event_exists_in_rm(e):
                raise UniqueEventRecordBroken()

    def _check_if_event_exists_in_rm(self, event: EventRecord) -> bool:
        exists = any(
            True
            for e in self.record_manager.heap
            if e.stream_id == event.stream_id and e.number == event.number
        )
        return exists


class UniqueEventRecordBroken(Exception):
    pass
