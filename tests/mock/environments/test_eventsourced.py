import pytest
import uuid

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import Identity
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.infrastructure.mappers import Mapper
from domainpy.utils.bus import Bus
from domainpy.utils.bus_subscribers import BasicSubscriber
from domainpy.utils.registry import Registry
from domainpy.utils.bus_adapters import ApplicationBusAdapter, ProjectionBusAdapter
from domainpy.mock.environments.eventsourced import EventSourcedEnvironmentTestAdapter


class Environment(EventSourcedEnvironmentTestAdapter):

    def setup_registry(self, registry: Registry, event_store: EventStore, setupargs: dict) -> None:
        pass
    
    def setup_projection_bus(self, projection_bus: ProjectionBusAdapter, registry: Registry, setupargs: dict) -> None:
        pass

    def setup_handler_bus(self, handler_bus: ApplicationBusAdapter, registry: Registry, setupargs: dict) -> None:
        pass

    def setup_resolver_bus(self, resolver_bus: ApplicationBusAdapter, publisher_integration_bus: Bus[IntegrationEvent], setupargs: dict) -> None:
        pass


class Aggregate(AggregateRoot):
    def mutate(self, event: DomainEvent) -> None:
        pass


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
def aggregate_id():
    return str(uuid.uuid4())

@pytest.fixture
def aggregate(aggregate_id):
    return Aggregate(Identity.from_text(aggregate_id))

@pytest.fixture
def event(aggregate):
    return aggregate.__stamp__(DomainEvent)(
        __trace_id__ = 'tid', some_property='x'
    )

@pytest.fixture
def integration():
    return IntegrationEvent(
        __resolve__ = 'success',
        __error__ = None,
        __timestamp__ = 0.0,
        some_property = 'x'
    )

@pytest.fixture
def command():
    return ApplicationCommand(
        __timestamp__ = 0.0,
        __trace_id__ = 'tid'
    )

def test_event_store_given_has_event(command_mapper, integration_mapper, event_mapper, aggregate_id, event):
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    env.given(event)
    env.then.domain_events.assert_has_event(event.__class__, aggregate_type=Aggregate, aggregate_id=aggregate_id)
    env.then.domain_events.assert_has_event_once(event.__class__)
    env.then.domain_events.assert_has_event_n_times(event.__class__, times=1)
    env.then.domain_events.assert_has_event_with(event.__class__, some_property='x')

def test_event_store_has_event_fails(command_mapper, integration_mapper, event_mapper):
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    with pytest.raises(AssertionError):
        env.then.domain_events.assert_has_event(DomainEvent)

    with pytest.raises(AssertionError):
        env.then.domain_events.assert_has_event_once(DomainEvent)

    with pytest.raises(AssertionError):
        env.then.domain_events.assert_has_event_n_times(DomainEvent, times=1)

    with pytest.raises(AssertionError):
        env.then.domain_events.assert_has_event_with(DomainEvent, some_property='x')

def test_event_store_has_not_event(command_mapper, integration_mapper, event_mapper):
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )
    env.then.domain_events.assert_has_not_event(DomainEvent)

def test_integrations_has_integration(command_mapper, integration_mapper, event_mapper, integration):
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    env.integration_publisher_bus.publish(integration)
    env.then.integration_events.assert_has_integration(IntegrationEvent)
    env.then.integration_events.assert_has_integration_with(IntegrationEvent, some_property='x')

def test_integrations_has_not_integration(command_mapper, integration_mapper, event_mapper):
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    env.then.integration_events.assert_has_not_integration(IntegrationEvent)

def test_when(command_mapper, integration_mapper, event_mapper, command):
    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    subscriber = BasicSubscriber()
    env.handler_bus.attach(subscriber)

    env.when(command)
    assert len(subscriber) == 1
