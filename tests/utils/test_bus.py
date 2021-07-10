
from domainpy.utils.bus import Bus, BasicSubscriber


def test_bus():
    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    bus = Bus()

    bs = BasicSubscriber()
    bus.attach(bs)

    bus.publish(some_message)

    assert len(bs) == 1
    assert bs[0] == some_message
    