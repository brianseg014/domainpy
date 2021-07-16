import pytest
import typing

from domainpy.utils.bus import Bus, ISubscriber
from domainpy.utils.bus_subscribers import BasicSubscriber


def test_bus():
    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    bus = Bus()

    sub = BasicSubscriber()
    bus.attach(sub)

    bus.publish(some_message)

    assert len(sub) == 1
    assert sub[0] == some_message
    
def test_bus_publish_exception():
    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    class ErrorSubsciber(ISubscriber[typing.Any]):
        def __route__(self, message: typing.Any):
            if message == some_message:
                raise Exception()

    suberr = ErrorSubsciber()
    sub = BasicSubscriber()

    bus = Bus(publish_exceptions=Exception)
    bus.attach(suberr)
    bus.attach(sub)

    bus.publish(some_message)

    assert len(sub) == 2

def test_bus_pass_exception():
    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    class ErrorSubsciber(ISubscriber[typing.Any]):
        def __route__(self, message: typing.Any):
            raise Exception()

    bus = Bus()
    bus.attach(ErrorSubsciber())

    with pytest.raises(Exception):
        bus.publish(some_message)