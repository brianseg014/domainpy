import pytest

from domainpy.domain.model.event import DomainEvent
from domainpy.utils.data import ImmutableError

def test_event_equality():
    a = DomainEvent(
        __stream_id__='a',
        __number__=1,
        __timestamp__=0.0,
        __version__=1
    )
    b = DomainEvent(
        __stream_id__='a',
        __number__=1,
        __timestamp__=0.0,
        __version__=1
    )
    assert a == b

def test_event_inequality():
    a = DomainEvent(
        __stream_id__='a',
        __number__=1,
        __timestamp__=0.0,
        __version__=1
    )
    b = DomainEvent(
        __stream_id__='b',
        __number__=1,
        __timestamp__=0.0,
        __version__=1
    )
    assert a != b

def test_event_immutability():
    a = DomainEvent(
        __stream_id__='a',
        __number__=1,
        __timestamp__=0.0,
        __version__=1
    )
    with pytest.raises(ImmutableError):
        a.some_property = 'x'
