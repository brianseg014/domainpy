from __future__ import annotations

import datetime
import typing

if typing.TYPE_CHECKING:
    from domainpy.infrastructure.eventsourced.recordmanager import (
        EventRecordManager,
    )
    from domainpy.utils.bus import Bus

from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.eventsourced.eventstream import EventStream
from domainpy.infrastructure.mappers import Mapper


class EventStore:
    def __init__(
        self,
        event_mapper: Mapper,
        record_manager: EventRecordManager,
        bus: Bus,
    ) -> None:
        self.event_mapper = event_mapper
        self.record_manager = record_manager
        self.bus = bus

    def store_events(self, stream: EventStream) -> None:
        with self.record_manager.session() as session:
            for e in stream:
                session.append(self.event_mapper.serialize(e))

            session.commit()

            for e in stream:
                self.bus.publish(e)

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

        events = self.record_manager.get_records(
            stream_id=stream_id,
            topic=topic,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            from_number=from_number,
            to_number=to_number,
        )

        stream = EventStream()
        for e in events:
            stream.append(self.event_mapper.deserialize(e))

        return stream
