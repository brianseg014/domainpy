from datetime import datetime
from domainpy.domain.model.event import DomainEvent
import uuid
import pytest
from unittest import mock

from domainpy.infrastructure.records import EventRecord
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.managers.memory import MemoryEventRecordManager
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.utils.bus import Bus
from domainpy.utils.bus_subscribers import BasicSubscriber


@pytest.fixture
def event_mapper():
    mapper = Mapper(transcoder=Transcoder())
    mapper.register(DomainEvent)
    return mapper

@pytest.fixture
def record_manager():
    return MemoryEventRecordManager()

@pytest.fixture
def bus_subscriber():
    return BasicSubscriber()

@pytest.fixture
def bus(bus_subscriber):
    bus = Bus()
    bus.attach(bus_subscriber)
    return bus

@pytest.fixture
def event():
    return DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0,
        __trace_id__ = 'tid',
        __context__ = 'ctx',
        __version__=1
    )

def test_store_events(event_mapper, record_manager, bus, bus_subscriber, event):
    es = EventStore(
        event_mapper=event_mapper,
        record_manager=record_manager,
        bus=bus
    )
    es.store_events([event])

    records = record_manager.get_records(event.__stream_id__)

    assert len(list(records)) == 1
    assert len(bus_subscriber) == 1

def test_get_events(event_mapper, record_manager, bus, event):
    with record_manager.session() as session:
        session.append(event_mapper.serialize(event))
        session.commit()

    es = EventStore(
        event_mapper=event_mapper,
        record_manager=record_manager,
        bus=bus
    )
    events = es.get_events(stream_id=event.__stream_id__)

    assert len(events) == 1
    assert events[0] == event