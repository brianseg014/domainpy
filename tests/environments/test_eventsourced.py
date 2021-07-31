

import pytest
import typing
from unittest import mock

from domainpy.typing.application import SystemMessage

from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.exceptions import DomainError
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.recordmanager import EventRecordManager
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.environments.eventsourced import EventSourcedEnvironment
from domainpy.exceptions import ConcurrencyError
from domainpy.utils.bus import Bus, ISubscriber, Message
from domainpy.utils.registry import Registry
from domainpy.utils.bus_adapters import ApplicationBusAdapter, ProjectionBusAdapter, PublisherBusAdapter


class Environment(EventSourcedEnvironment):
    
    def setup_event_record_manager(self, setupargs: dict) -> EventRecordManager:
        pass

    def setup_registry(self, registry: Registry, event_store: EventStore, setupargs: dict) -> None:
        pass

    def setup_projection_bus(self, projection_bus: ProjectionBusAdapter, registry: Registry, setupargs: dict) -> None:
        pass

    def setup_handler_bus(self, handler_bus: ApplicationBusAdapter, registry: Registry, setupargs: dict) -> None:
        pass

    def setup_resolver_bus(self, resolver_bus: ApplicationBusAdapter, publisher_integration_bus: Bus[IntegrationEvent], setupargs: dict) -> None:
        pass

    def setup_domain_publisher_bus(self, domain_publisher_bus: PublisherBusAdapter[DomainEvent], event_mapper: Mapper, setupargs: dict) -> None:
        pass

    def setup_integration_publisher_bus(self, integration_publisher_bus: PublisherBusAdapter[IntegrationEvent], integration_mapper: Mapper, setupargs: dict) -> None:
        pass


class StorySubscriber(ISubscriber[SystemMessage]):

    def __init__(self, name: str, story: typing.List[str]):
        self.name = name
        self.story = story

    def __route__(self, message: SystemMessage):
        self.story.append(self.name)
        

@pytest.fixture
def command_mapper():
    return Mapper(
        transcoder=Transcoder()
    )

@pytest.fixture
def integration_mapper():
    return Mapper(
        transcoder=Transcoder()
    )

@pytest.fixture
def event_mapper():
    return Mapper(
        transcoder=Transcoder()
    )

@pytest.fixture
def event():
    return DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0,
        __trace_id__ = 'tid'
    )

def test_bus_sequence(command_mapper, integration_mapper, event_mapper, event):
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    story = []
    env.handler_bus.attach(StorySubscriber('handler', story))
    env.projection_bus.attach(StorySubscriber('projection', story))
    env.integration_publisher_bus.attach(StorySubscriber('integration', story))
    env.resolver_bus.attach(StorySubscriber('resolver', story))
    env.domain_publisher_bus.attach(StorySubscriber('domain', story))
    
    env.event_store.store_events([event])

    assert story == ['domain', 'projection', 'resolver', 'handler']

def test_bus_handle(command_mapper, integration_mapper, event_mapper, event):
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
    )

    story = []
    env.resolver_bus.attach(StorySubscriber('resolver', story))
    env.handler_bus.attach(StorySubscriber('handler', story))

    env.handle(event)

    assert story == ['resolver', 'handler']

def test_publish_domain_error(command_mapper, integration_mapper, event_mapper, event):
    error = DomainError()
    def router(message):
        if message == event:
            raise error

    handler = mock.MagicMock()
    handler.__route__ = mock.Mock(side_effect=router)
    
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
    )

    env.handler_bus.attach(handler)

    env.handle(event)

    handler.__route__.assert_called_with(error)

def test_publish_retry_on_concurrency_error(command_mapper, integration_mapper, event_mapper, event):
    story = []

    class Handler(ISubscriber):
        def __route__(self, message: Message):
            if len(story) <= 1:
                story.append('raised')
                raise ConcurrencyError()
    
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
    )

    handler = Handler()
    env.handler_bus.attach(handler)

    env.handle(event)

    assert story == ['raised', 'raised']

def test_publish_raise_concurrency_error_if_exahusted(command_mapper, integration_mapper, event_mapper, event):
    story = []

    class Handler(ISubscriber):
        def __route__(self, message: Message):
            if len(story) <= 5:
                story.append('raised')
                raise ConcurrencyError()
    
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
    )

    handler = Handler()
    env.handler_bus.attach(handler)

    with pytest.raises(ConcurrencyError):
        env.handle(event)

def test_bus_handle_fails_if_trace_id_is_None(command_mapper, integration_mapper, event_mapper):
    event = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0,
        __trace_id__ = None
    )

    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
    )

    with pytest.raises(TypeError):
        env.handle(event)