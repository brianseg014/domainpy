import typing

from domainpy.bootstrap import ServiceBus
from domainpy.application.command import ApplicationCommand
from domainpy.application.service import ApplicationService
from domainpy.application.projection import Projection
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.exceptions import DomainError
from domainpy.infrastructure.publishers.base import IPublisher
from domainpy.typing.application import SystemMessage


def test_handle():
    story = []

    service_bus = ServiceBus()
    command = ApplicationCommand(__timestamp__=0.0)

    class TestProjection(Projection):
        def project(self, event: DomainEvent):
            story.append(('projection', event))

    class TestHandler(ApplicationService):
        def handle(self, message: SystemMessage) -> None:
            story.append(('handle', message))

    class TestResolver(ApplicationService):
        def handle(self, message: SystemMessage) -> None:
            story.append(('resolver', message))

    class TestPublisher(IPublisher):
        def publish(self, messages: typing.Union[SystemMessage, typing.Sequence[SystemMessage]]):
            story.append(('publish', messages))

    projection = TestProjection()
    handler = TestHandler()
    resolver = TestResolver()
    publisher = TestPublisher()

    service_bus.add_projection(projection)
    service_bus.add_handler(handler)
    service_bus.add_resolver(resolver)
    service_bus.add_event_publisher(publisher)

    service_bus.handle(command)

    assert story == [('resolver', command), ('handle', command)]

def test_handle_with_event():
    story = []

    service_bus = ServiceBus()
    command = ApplicationCommand(__timestamp__=0.0)
    event = DomainEvent(__stream_id__='sid', __number__=1, __timestamp__=0.0)

    class TestProjection(Projection):
        def project(self, event: DomainEvent):
            story.append(('projection', event))

    class TestHandler(ApplicationService):
        def handle(self, message: SystemMessage) -> None:
            story.append(('handle', message))

            if isinstance(message, ApplicationCommand):
                service_bus.event_bus.publish(event)

    class TestResolver(ApplicationService):
        def handle(self, message: SystemMessage) -> None:
            story.append(('resolver', message))

    class TestPublisher(IPublisher):
        def publish(self, messages: typing.Union[SystemMessage, typing.Sequence[SystemMessage]]):
            story.append(('publish', messages))

    projection = TestProjection()
    handler = TestHandler()
    resolver = TestResolver()
    publisher = TestPublisher()

    service_bus.add_projection(projection)
    service_bus.add_handler(handler)
    service_bus.add_resolver(resolver)
    service_bus.add_event_publisher(publisher)

    service_bus.handle(command)

    assert story == [
        ('resolver', command), ('handle', command),
        ('publish', event), ('projection', event), ('resolver', event), ('handle', event)
    ]

def test_handle_with_error():
    story = []

    service_bus = ServiceBus()
    command = ApplicationCommand(__timestamp__=0.0)
    error = DomainError()

    class TestProjection(Projection):
        def project(self, event: DomainEvent):
            story.append(('projection', event))

    class TestHandler(ApplicationService):
        def handle(self, message: SystemMessage) -> None:
            story.append(('handle', message))
            
            if isinstance(message, ApplicationCommand):
                raise error

    class TestResolver(ApplicationService):
        def handle(self, message: SystemMessage) -> None:
            story.append(('resolver', message))

    class TestPublisher(IPublisher):
        def publish(self, messages: typing.Union[SystemMessage, typing.Sequence[SystemMessage]]):
            story.append(('publish', messages))

    projection = TestProjection()
    handler = TestHandler()
    resolver = TestResolver()
    publisher = TestPublisher()

    service_bus.add_projection(projection)
    service_bus.add_handler(handler)
    service_bus.add_resolver(resolver)
    service_bus.add_event_publisher(publisher)

    service_bus.handle(command)

    assert story == [
        ('resolver', command), ('handle', command),
        ('resolver', error), ('handle', error)
    ]
