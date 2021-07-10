from datetime import datetime
import uuid
import pytest
from unittest import mock

from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.records import EventRecord
from domainpy.infrastructure.eventsourced.eventstore import EventStore


@pytest.fixture
def event_mapper():
    return mock.MagicMock()

@pytest.fixture
def record_manager():
    return mock.MagicMock()

@pytest.fixture
def bus():
    return mock.MagicMock()

def test_store_events(event_mapper, record_manager, bus):
    e = DomainEvent()

    es = EventStore(
        event_mapper=event_mapper,
        record_manager=record_manager,
        bus=bus
    )
    es.store_events([e])

    record_manager.session.assert_called()
    event_mapper.serialize.assert_called_once_with(e)
    bus.publish.assert_called_once_with(e)

def test_get_events(event_mapper, record_manager, bus):
    stream_id = str(uuid.uuid4())
    er = EventRecord(
        stream_id=stream_id,
        number=0,
        topic='some-topic',
        version=1,
        timestamp=datetime.timestamp(datetime.now()),
        trace_id=str(uuid.uuid4()),
        message='event',
        context='some-context',
        payload={}
    )
    record_manager.get_records = mock.Mock(return_value=[er])

    e = DomainEvent(__stream_id__=stream_id, __number__=0)
    event_mapper.deserialize = mock.Mock(return_value=e)

    es = EventStore(
        event_mapper=event_mapper,
        record_manager=record_manager,
        bus=bus
    )
    events = es.get_events(stream_id=stream_id)

    assert len(events) == 1
    assert events[0] == e
