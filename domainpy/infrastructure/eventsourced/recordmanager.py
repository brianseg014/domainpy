from __future__ import annotations

import abc
import typing
import datetime
import contextlib

from domainpy.infrastructure.records import EventRecord


class EventRecordManager(abc.ABC):
    @abc.abstractmethod
    def session(self) -> Session:
        pass  # pragma: no cover

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
    ) -> typing.Generator[EventRecord, None, None]:
        pass  # pragma: no cover


class Session(contextlib.AbstractContextManager):
    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.rollback()

    @abc.abstractmethod
    def append(self, event_record: EventRecord) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def commit(self) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def rollback(self) -> None:
        pass  # pragma: no cover
