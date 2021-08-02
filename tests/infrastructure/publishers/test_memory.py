
from domainpy.application.command import ApplicationCommand
from domainpy.infrastructure.publishers.memory import MemoryPublisher


def test_publish():
    command = ApplicationCommand(
        __timestamp__=0.0,
        __trace_id__='tid'
    )

    pub = MemoryPublisher()
    pub.publish(command)