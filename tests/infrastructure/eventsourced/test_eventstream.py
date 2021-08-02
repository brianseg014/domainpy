
import datetime

from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.eventsourced.eventstream import EventStream


def test_substream_topic():
    class SomeEvent(DomainEvent):
        pass

    class SomeOtherEvent(DomainEvent):
        pass

    some_event = SomeEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0
    )
    some_other_event = SomeOtherEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0
    )

    es = EventStream()
    es.append(some_event)
    es.append(some_other_event)

    subes = es.substream(topic_type=some_other_event.__class__)

    # Should only event_type_2 be present
    assert len(subes) == 1
    assert subes[0].__class__ == some_other_event.__class__

def test_substream_from_number():
    event0 = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 0,
        __timestamp__ = 0.0
    )
    event1 = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0
    )

    es = EventStream()
    es.extend([event0, event1])

    subes = es.substream(from_number=1)

    # Should only number=1 be present
    assert len(subes) == 1
    assert subes[0].__number__ == 1

def test_substream_to_number():
    event0 = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 0,
        __timestamp__ = 0.0
    )
    event1 = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0
    )

    es = EventStream()
    es.extend([event0, event1])

    subes = es.substream(to_number=0)

    # Should only number=0 be present
    assert len(subes) == 1
    assert subes[0].__number__ == 0

def test_substream_from_timestamp():
    timestamp_60_mins_ago = datetime.datetime.timestamp(datetime.datetime.now() - datetime.timedelta(minutes=60))
    timestamp_now = datetime.datetime.timestamp(datetime.datetime.now())

    event0 = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 0,
        __timestamp__ = timestamp_60_mins_ago
    )
    event1 = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = timestamp_now
    )

    es = EventStream()
    es.extend([event0, event1])

    timestamp_30_mins_ago=datetime.datetime.timestamp(datetime.datetime.now() - datetime.timedelta(minutes=30))
    subes = es.substream(from_timestamp=timestamp_30_mins_ago)

    assert len(subes) == 1
    assert subes[0].__timestamp__ == timestamp_now

def test_substream_to_timestamp():
    timestamp_60_mins_ago = datetime.datetime.timestamp(datetime.datetime.now() - datetime.timedelta(minutes=60))
    timestamp_now = datetime.datetime.timestamp(datetime.datetime.now())

    event0 = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 0,
        __timestamp__ = timestamp_60_mins_ago
    )
    event1 = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = timestamp_now
    )

    es = EventStream()
    es.extend([event0, event1])

    timestamp_30_mins_ago=datetime.datetime.timestamp(datetime.datetime.now() - datetime.timedelta(minutes=30))
    subes = es.substream(to_timestamp=timestamp_30_mins_ago)

    assert len(subes) == 1
    assert subes[0].__timestamp__ == timestamp_60_mins_ago