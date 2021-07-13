
from domainpy.infrastructure.publishers.memory import MemoryPublisher


def test_publish():
    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    pub = MemoryPublisher()
    pub.publish(some_message)