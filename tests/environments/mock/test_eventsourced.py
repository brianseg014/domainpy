import pytest
import uuid

from domainpy.environments.mock.eventsourced import MockEventSourcedEnvironment
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.mappers import CommandMapper, EventMapper, IntegrationMapper
from domainpy.utils.bus import BasicSubscriber


def test_event_store_given_has_event():
    command_mapper = CommandMapper()
    integration_mapper = IntegrationMapper('some_context')
    event_mapper = EventMapper('some_context')

    SomeDomainEvent = type('SomeDomainEventType', (DomainEvent,), { '__annotations__': { 'some_property': str } })
    event_mapper.register(SomeDomainEvent)

    env = MockEventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )
    
    stream_id = str(uuid.uuid4())
    env.given(stream_id, SomeDomainEvent(some_property='x'))
    env.then.event_store.assert_has_event(stream_id, SomeDomainEvent)
    env.then.event_store.assert_has_event_once(stream_id, SomeDomainEvent)
    env.then.event_store.assert_has_event_n(stream_id, SomeDomainEvent, 1)
    env.then.event_store.assert_has_event_with(stream_id, SomeDomainEvent, some_property='x')

def test_event_store_has_event_fails():
    command_mapper = CommandMapper()
    integration_mapper = IntegrationMapper('some_context')
    event_mapper = EventMapper('some_context')

    env = MockEventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    stream_id = str(uuid.uuid4())
    with pytest.raises(AssertionError):
        env.then.event_store.assert_has_event(stream_id, DomainEvent)

    with pytest.raises(AssertionError):
        env.then.event_store.assert_has_event_once(stream_id, DomainEvent)

    with pytest.raises(AssertionError):
        env.then.event_store.assert_has_event_n(stream_id, DomainEvent, 1)

    with pytest.raises(AssertionError):
        env.then.event_store.assert_has_event_with(stream_id, DomainEvent, some_property='x')

def test_event_store_has_not_event():
    command_mapper = CommandMapper()
    integration_mapper = IntegrationMapper('some_context')
    event_mapper = EventMapper('some_context')

    env = MockEventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    stream_id = str(uuid.uuid4())
    env.then.event_store.assert_has_not_event(stream_id, DomainEvent)

def test_integrations_has_integration():
    command_mapper = CommandMapper()
    integration_mapper = IntegrationMapper('some_context')
    event_mapper = EventMapper('some_context')

    env = MockEventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    env.publisher_integration_bus.publish(IntegrationEvent(some_property='x'))
    env.then.integration_events.has_integration(IntegrationEvent)
    env.then.integration_events.has_integration_with(IntegrationEvent, some_property='x')

def test_integrations_has_not_integration():
    command_mapper = CommandMapper()
    integration_mapper = IntegrationMapper('some_context')
    event_mapper = EventMapper('some_context')

    env = MockEventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    env.then.integration_events.has_not_integration(IntegrationEvent)

def test_when():
    command_mapper = CommandMapper()
    integration_mapper = IntegrationMapper('some_context')
    event_mapper = EventMapper('some_context')

    env = MockEventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    subscriber = BasicSubscriber()
    env.handler_bus.attach(subscriber)

    env.when(ApplicationCommand())
    assert len(subscriber) == 1
