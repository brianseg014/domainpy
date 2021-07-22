from __future__ import annotations

import abc
import typing
import datetime
import contextlib

from domainpy.infrastructure.records import EventRecord


class EventRecordManager(abc.ABC):
    @abc.abstractmethod
    def session(self) -> Session:
        pass

    @abc.abstractmethod
    def get_records(
        self,
        stream_id: str,
        *,
        topic: str = None,
        from_timestamp: datetime.datetime = None,
        to_timestamp: datetime.datetime = None,
        from_number: int = None,
        to_number: int = None,
    ) -> typing.Tuple[EventRecord, ...]:
        pass


class Session(contextlib.AbstractContextManager):
    @abc.abstractmethod
    def append(self, event_record: EventRecord) -> None:
        pass
