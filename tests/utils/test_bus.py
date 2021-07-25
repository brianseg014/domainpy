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
