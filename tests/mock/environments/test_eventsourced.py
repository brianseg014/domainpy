import pytest
import uuid
from unittest import mock

from domainpy.mock.environments.eventsourced import EventSourcedEnvironmentTestAdapter
from domainpy.utils.bus_subscribers import BasicSubscriber

def test_event_store_given_has_event():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()

    DomainEvent = type(
        'DomainEvent', 
        (mock.MagicMock,),
        {}
    )

    env = EventSourcedEnvironmentTestAdapter(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )
    
    stream_id = str(uuid.uuid4())
    
    event = DomainEvent()
    event.__stream_id__=stream_id
    event.some_property='x'

    env.given(event)
    env.then.domain_events.assert_has_event(event.__class__, stream_id=stream_id)
    env.then.domain_events.assert_has_event_once(event.__class__)
    env.then.domain_events.assert_has_event_n(event.__class__, n=1)
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

    env = EventSourcedEnvironmentTestAdapter(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    with pytest.raises(AssertionError):
        env.then.domain_events.assert_has_event(DomainEvent)

    with pytest.raises(AssertionError):
        env.then.domain_events.assert_has_event_once(DomainEvent)

    with pytest.raises(AssertionError):
        env.then.domain_events.assert_has_event_n(DomainEvent, 1)

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

    env = EventSourcedEnvironmentTestAdapter(
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

    env = EventSourcedEnvironmentTestAdapter(
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

    env = EventSourcedEnvironmentTestAdapter(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    env.then.integration_events.assert_has_not_integration(IntegrationEvent)

@mock.patch('domainpy.environments.eventsourced.MapperSet')
def test_when(MapperSet):
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

    mapper_set_instance = MapperSet.return_value
    mapper_set_instance.deserialize = mock.Mock(return_value=command)

    env = EventSourcedEnvironmentTestAdapter(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    subscriber = BasicSubscriber()
    env.handler_bus.attach(subscriber)

    env.when(command)
    assert len(subscriber) == 1