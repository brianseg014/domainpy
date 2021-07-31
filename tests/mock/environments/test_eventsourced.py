import pytest
import uuid
from unittest import mock

from domainpy.application.integration import IntegrationEvent
from domainpy.infrastructure.eventsourced.eventstore import EventStore
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


def test_event_store_given_has_event():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()

    aggreagte_id = str(uuid.uuid4())

    Aggregate = type(
        'Aggregate',
        (mock.MagicMock,),
        {}
    )
    Aggregate.__name__ = 'Aggregate'
    Aggregate.create_stream_id = mock.Mock(return_value=f'{aggreagte_id}:Aggregate')

    DomainEvent = type(
        'DomainEvent', 
        (mock.MagicMock,),
        {}
    )

    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )
    
    event = DomainEvent()
    event.__trace_id__='tid'
    event.__stream_id__=f'{aggreagte_id}:{Aggregate.__name__}'
    event.some_property='x'

    env.given(event)
    env.then.domain_events.assert_has_event(event.__class__, aggregate_type=Aggregate, aggregate_id=aggreagte_id)
    env.then.domain_events.assert_has_event_once(event.__class__)
    env.then.domain_events.assert_has_event_n_times(event.__class__, times=1)
    env.then.domain_events.assert_has_event_with(event.__class__, some_property='x')

def test_event_store_has_event_fails():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()

    DomainEvent = type(
        'DomainEvent', 
        (mock.MagicMock,),
        {}
    )

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

def test_event_store_has_not_event():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()

    DomainEvent = type(
        'DomainEvent', 
        (mock.MagicMock,),
        {}
    )

    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )
    env.then.domain_events.assert_has_not_event(DomainEvent)

def test_integrations_has_integration():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()

    IntegrationEvent = type(
        'IntegrationEvent',
        (mock.MagicMock,),
        { }
    )

    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    integration = IntegrationEvent()
    integration.some_property = 'x'
    env.integration_publisher_bus.publish(integration)
    env.then.integration_events.assert_has_integration(IntegrationEvent)
    env.then.integration_events.assert_has_integration_with(IntegrationEvent, some_property='x')

def test_integrations_has_not_integration():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()

    IntegrationEvent = type(
        'IntegrationEvent',
        (mock.MagicMock,),
        { }
    )

    env = Environment(
        context='some_context',
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    env.then.integration_events.assert_has_not_integration(IntegrationEvent)

def test_when():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()

    ApplicationCommand = type(
        'ApplicationComand',
        (mock.MagicMock,),
        { }
    )

    command = ApplicationCommand()
    command.__trace_id__ = 'tid'

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