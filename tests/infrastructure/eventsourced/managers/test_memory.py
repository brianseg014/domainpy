import pytest
import uuid
import datetime
import dataclasses

from domainpy import exceptions as excs
from domainpy.infrastructure.eventsourced.managers.memory import MemoryEventRecordManager
from domainpy.infrastructure.records import EventRecord


@pytest.fixture
def stream_id():
    return str(uuid.uuid4())

@pytest.fixture
def  event_record(stream_id):
    return EventRecord(
        stream_id=stream_id,
        number=0,
        topic='some-topic',
        version=1,
        timestamp=datetime.datetime.now(),
        trace_id=uuid.uuid4(),
        message='event',
        context='some-context',
        payload={}
    )

def test_append_commit(event_record):
    rm = MemoryEventRecordManager()

    with rm.session() as session:
        session.append(
            event_record
        )
        session.commit()

    assert len(rm.heap) == 1

def test_append_rollback(event_record):
    rm = MemoryEventRecordManager()

    with rm.session() as session:
        session.append(
            event_record
        )

    assert len(rm.heap) == 0

def test_append_fail_on_concurrency(event_record):
    rm = MemoryEventRecordManager()
    rm.heap.append(event_record)

    with pytest.raises(excs.ConcurrencyError):
        with rm.session() as session:
            session.append(
                event_record
            )
            session.commit()

def test_get_records(stream_id, event_record):
    rm = MemoryEventRecordManager()
    rm.heap.append(event_record)

    events = rm.get_records(stream_id)
    assert len(list(events)) == 1

    events = rm.get_records(stream_id, 
        topic=event_record.topic,
        from_timestamp=event_record.timestamp,
        to_timestamp=event_record.timestamp,
        from_number=event_record.number,
        to_number=event_record.number
    )
    assert len(list(events)) == 1

def test_get_records_filtering_number(stream_id, event_record):
    event_record_2 = dataclasses.replace(event_record, number=1)

    rm = MemoryEventRecordManager()
    rm.heap.append(event_record)
    rm.heap.append(event_record_2)

    events = rm.get_records(stream_id, from_number=0, to_number=0)
    assert len(list(events)) == 1
