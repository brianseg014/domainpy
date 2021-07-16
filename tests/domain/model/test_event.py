import pytest

from domainpy.domain.model.event import DomainEvent

def test_event_equality():
    a = DomainEvent(
        __stream_id__='a',
        __number__=1,
        __timestamp__=0.0
    )
    b = DomainEvent(
        __stream_id__='a',
        __number__=1,
        __timestamp__=0.0
    )
    assert a == b

def test_event_inequality():
    a = DomainEvent(
        __stream_id__='a',
        __number__=1,
        __timestamp__=0.0
    )
    b = DomainEvent(
        __stream_id__='b',
        __number__=1,
        __timestamp__=0.0
    )
    assert a != b

def test_event_immutability():
    a = DomainEvent(
        __stream_id__='a',
        __number__=1,
        __timestamp__=0.0
    )
    with pytest.raises(AttributeError):
        a.some_property = 'x'