
from datetime import datetime
import pytest
import uuid
from unittest import mock

from domainpy.application.service import ApplicationService
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.mappers import EventMapper
from domainpy.utils.registry import Registry
from domainpy.utils.bus import Bus
from domainpy.utils.bus_subscribers import ApplicationServiceSubscriber
from domainpy.test import Environment

def test_setup():
    env = Environment(
        event_mapper=EventMapper('some-context')
    )

    @env.setup
    def setup(registry: Registry, handler_bus: Bus, resolver_bus: Bus, integration_bus: Bus):
        assert isinstance(registry, Registry)
        assert isinstance(handler_bus, Bus)
        assert isinstance(resolver_bus, Bus)
        assert isinstance(integration_bus, Bus)

    setup()

def test_event_store_has_event_success():
    event_mapper = EventMapper('some-context')

    stream_id = str(uuid.uuid4())
    
    SomeEvent = event_mapper.register(type('SomeEvent', (DomainEvent,), {}))
    SomeOtherEvent = event_mapper.register(type('SomeOtherEvent', (DomainEvent,), {}))

    env = Environment(
        event_mapper=event_mapper
    )
    env.setup(lambda *args, **kwargs: None)()

    env.given(stream_id, SomeEvent(__number__=0))
    env.then.event_store.has_event(stream_id, SomeEvent)
    env.then.event_store.has_event_once(stream_id, SomeEvent)
    env.then.event_store.has_event_n(stream_id, SomeEvent, 1)
    env.then.event_store.has_event_with(stream_id, SomeEvent, __number__=0)
    env.then.event_store.has_not_event(stream_id, SomeOtherEvent)

def test_event_store_has_event_fail():
    event_mapper = EventMapper('some-context')

    stream_id = str(uuid.uuid4())

    SomeEvent = type('SomeEvent', (DomainEvent,), {})
    SomeOtherEvent = event_mapper.register(type('SomeOtherEvent', (DomainEvent,), {}))

    env = Environment(
        event_mapper=event_mapper
    )
    env.setup(lambda *args, **kwargs: None)()

    env.given(stream_id, SomeOtherEvent())

    with pytest.raises(AssertionError):
        env.then.event_store.has_event(stream_id, SomeEvent)

    with pytest.raises(AssertionError):
        env.then.event_store.has_event_once(stream_id, SomeEvent)

    with pytest.raises(AssertionError):
        env.then.event_store.has_event_n(stream_id, SomeEvent, 1)

    with pytest.raises(AssertionError):
        env.then.event_store.has_event_with(stream_id, SomeEvent, __number__=1)

    with pytest.raises(AssertionError):
        env.then.event_store.has_not_event(stream_id, SomeOtherEvent)

def test_integrations_has_integration():
    event_mapper = EventMapper('some-context')

    SomeCommand = type('SomeCommand', (ApplicationCommand,), {})
    SomeIntegration = type('SomeIntegration', (IntegrationEvent,), {})
    SomeOtherIntegration = type('SomeOtherIntegration', (IntegrationEvent,), {})

    class SomeApplicationService(ApplicationService):

        def __init__(self, integration_bus: Bus):
            self.integration_bus = integration_bus

        def handle(self, _: SomeCommand):
            self.integration_bus.publish(
                SomeIntegration(
                    some_property='x'
                )
            )

    env = Environment(
        event_mapper=event_mapper
    )

    @env.setup
    def setup(registry: Registry, handler_bus: Bus, resolver_bus: Bus, integration_bus: Bus):
        handler_bus.attach(
            ApplicationServiceSubscriber(SomeApplicationService(integration_bus))
        )

    setup()

    env.when(SomeCommand())
    env.then.integration_events.has_integration(SomeIntegration)
    env.then.integration_events.has_integration_with(SomeIntegration, some_property='x')
    env.then.integration_events.has_not_integration(SomeOtherIntegration)

def test_integrations_has_integration_fails():
    event_mapper = EventMapper('some-context')

    SomeIntegration = type('SomeIntegration', (IntegrationEvent,), {})

    env = Environment(
        event_mapper=event_mapper
    )
    env.setup(lambda *args, **kwargs: None)()

    with pytest.raises(AssertionError):
        env.then.integration_events.has_integration(SomeIntegration)

    with pytest.raises(AssertionError):
        env.then.integration_events.has_integration_with(SomeIntegration, some_property='x')

def test_use_case():
    event_mapper = EventMapper('some-context')

    stream_id = str(uuid.uuid4())

    SomeCommand = type('SomeCommand', (ApplicationCommand,), {})
    SomeEvent = event_mapper.register(type('SomeEvent', (DomainEvent,), {}))
    SomeOtherEvent = event_mapper.register(type('SomeOtherEvent', (DomainEvent,), {}))
    SomeIntegration = type('SomeIntegration', (IntegrationEvent,), {})

    class SomeApplicationHandlerService(ApplicationService):

        def __init__(self, env: Environment):
            self.env = env

        def handle(self, some_command: SomeCommand):
            if isinstance(some_command, SomeCommand):
                self.env.event_store.store_events([
                    SomeOtherEvent(
                        __stream_id__=stream_id,
                        __number__=2,
                        __timestamp__=datetime.timestamp(datetime.now())
                    )
                ])

    class SomeApplicationResolverService(ApplicationService):

        def __init__(self, integration_bus: Bus):
            self.integration_bus = integration_bus

        def handle(self, some_other_event: SomeOtherEvent):
            if isinstance(some_other_event, SomeOtherEvent):
                self.integration_bus.publish(
                    SomeIntegration()
                )

    env = Environment(
        event_mapper=event_mapper
    )

    @env.setup
    def setup(registry: Registry, handler_bus: Bus, resolver_bus: Bus, integration_bus: Bus):
        handler_bus.attach(
            ApplicationServiceSubscriber(SomeApplicationHandlerService(env))
        )
        resolver_bus.attach(
            ApplicationServiceSubscriber(SomeApplicationResolverService(integration_bus))
        )

    setup()

    env.given(stream_id, SomeEvent())
    env.when(SomeCommand())
    env.then.event_store.has_event_n(stream_id, SomeEvent, 1)
    env.then.event_store.has_event(stream_id, SomeOtherEvent)
    env.then.integration_events.has_integration(SomeIntegration)

def test_tear_down():
    stream_id = str(uuid.uuid4())

    SomeEvent = type('SomeEvent', (DomainEvent,), {})

    env = Environment(
        event_mapper=EventMapper('some-context')
    )
    env.setup(lambda *args, **kwargs: None)()

    env.given(stream_id, SomeEvent())

    env.tear_down()

    env.then.event_store.has_not_event(stream_id, SomeEvent)