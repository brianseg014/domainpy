
from datetime import datetime, timedelta

from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.eventsourced.eventstream import EventStream


def test_substream_topic():
    event_type_1 = type('Event1', (DomainEvent,), {})
    event_type_2 = type('Event2', (DomainEvent,), {})

    es = EventStream()
    es.append(event_type_1())
    es.append(event_type_2())

    subes = es.substream(topic_type=event_type_2)

    # Should only event_type_2 be present
    assert len(subes) == 1
    assert subes[0].__class__ == event_type_2

def test_substream_from_number():
    e0 = DomainEvent(__number__=0)
    e1 = DomainEvent(__number__=1)

    es = EventStream()
    es.extend([e0, e1])

    subes = es.substream(from_number=1)

    # Should only number=1 be present
    assert len(subes) == 1
    assert subes[0].__number__ == 1

def test_substream_to_number():
    e0 = DomainEvent(__number__=0)
    e1 = DomainEvent(__number__=1)

    es = EventStream()
    es.extend([e0, e1])

    subes = es.substream(to_number=0)

    # Should only number=0 be present
    assert len(subes) == 1
    assert subes[0].__number__ == 0

def test_substream_from_timestamp():
    timestamp_60_mins_ago = datetime.timestamp(datetime.now() - timedelta(minutes=60))
    timestamp_now = datetime.timestamp(datetime.now())

    e0 = DomainEvent(__timestamp__=timestamp_60_mins_ago)
    e1 = DomainEvent(__timestamp__=timestamp_now)

    es = EventStream()
    es.extend([e0, e1])

    timestamp_30_mins_ago=datetime.timestamp(datetime.now() - timedelta(minutes=30))
    subes = es.substream(from_timestamp=timestamp_30_mins_ago)

    assert len(subes) == 1
    assert subes[0].__timestamp__ == timestamp_now

def test_substream_to_timestamp():
    timestamp_60_mins_ago = datetime.timestamp(datetime.now() - timedelta(minutes=60))
    timestamp_now = datetime.timestamp(datetime.now())

    e0 = DomainEvent(__timestamp__=timestamp_60_mins_ago)
    e1 = DomainEvent(__timestamp__=timestamp_now)

    es = EventStream()
    es.extend([e0, e1])

    timestamp_30_mins_ago=datetime.timestamp(datetime.now() - timedelta(minutes=30))
    subes = es.substream(to_timestamp=timestamp_30_mins_ago)

    assert len(subes) == 1
    assert subes[0].__timestamp__ == timestamp_60_mins_ago
