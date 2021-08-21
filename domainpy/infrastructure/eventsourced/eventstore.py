from __future__ import annotations

import datetime
import typing

from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.eventsourced.eventstream import EventStream
from domainpy.infrastructure.mappers import Mapper

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.infrastructure.eventsourced.recordmanager import (
        EventRecordManager,
    )
    from domainpy.utils.bus import Bus


class EventStore:
    def __init__(
        self,
        event_mapper: Mapper,
        record_manager: EventRecordManager,
        *,
        bus: Bus = None,
    ) -> None:
        self.event_mapper = event_mapper
        self.record_manager = record_manager
        self.bus = bus

    def store_events(self, stream: EventStream) -> None:
        with self.record_manager.session() as session:
            for event in stream:
                session.append(self.event_mapper.serialize(event))

            session.commit()

        if self.bus is not None:
            for event in stream:
                self.bus.publish(event)

    def get_events(
        self,
        stream_id: str,
        *,
        event_type: typing.Type[DomainEvent] = None,
        from_timestamp: datetime.datetime = None,
        to_timestamp: datetime.datetime = None,
        from_number: int = None,
        to_number: int = None,
    ) -> EventStream:
        topic: typing.Optional[str]

        if event_type is not None:
            topic = event_type.__name__
        else:
            topic = None

        records = self.record_manager.get_records(
            stream_id=stream_id,
            topic=topic,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            from_number=from_number,
            to_number=to_number,
        )

        stream = EventStream()
        for record in records:
            stream.append(
                typing.cast(DomainEvent, self.event_mapper.deserialize(record))
            )

        return stream
