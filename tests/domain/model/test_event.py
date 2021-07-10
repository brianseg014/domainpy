
from domainpy.domain.model.event import DomainEvent

def test_event_equality():
    class BasicEvent(DomainEvent):
        some_property: str

    a = BasicEvent(
        __stream_id__ = 'id',
        __number__ = 0,
        some_property='x'
    )
    b = BasicEvent(
        __stream_id__ = 'id',
        __number__ = 0,
        some_property='x'
    )
    assert a == b
