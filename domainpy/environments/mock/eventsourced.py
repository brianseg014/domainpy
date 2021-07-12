import sys
import types
import json
import datetime
import itertools
import dataclasses

from domainpy.typing import SystemMessage
from domainpy.environments.eventsourced import EventSourcedEnvironment
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.mappers import CommandMapper, IntegrationMapper, EventMapper
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.managers.memory import MemoryEventRecordManager
from domainpy.utils.bus import Bus, BasicSubscriber
from domainpy.utils.registry import Registry

@dataclasses.dataclass(frozen=True)
class Then:
    event_store: 'EventStoreTestExpression'
    integration_events: 'IntegrationEventsTestExpression'


class MockEventSourcedEnvironment(EventSourcedEnvironment):

    def __init__(self, 
        command_mapper: CommandMapper, 
        integration_mapper: IntegrationMapper, 
        event_mapper: EventMapper
    ) -> None:
        super().__init__(
            command_mapper=command_mapper, 
            integration_mapper=integration_mapper, 
            event_mapper=event_mapper, 
            event_store_record_manager=MemoryEventRecordManager()
        )

        self.sequences = {}

        self.domain_events = BasicSubscriber[DomainEvent]()
        self.event_store_bus.attach(self.domain_events)

        self.integration_events = BasicSubscriber[IntegrationEvent]()
        self.integration_bus.attach(self.integration_events)

    def given(self, stream_id: str, event: DomainEvent):
        sequence = self.sequences.setdefault(stream_id, itertools.count(start=0, step=1))

        event.__dict__.update({
            '__stream_id__': stream_id,
            '__number__': next(sequence),
            '__timestamp__': datetime.datetime.timestamp(datetime.datetime.now())
        })

        self.event_store.store_events([event])

    def when(self, message: SystemMessage):
        self.handler_bus.publish(message)

    @property
    def then(self):
        return Then(
            event_store=EventStoreTestExpression(self.domain_events, self.event_store),
            integration_events=IntegrationEventsTestExpression(self.integration_events)
        )

    
class EventStoreTestExpression:

    def __init__(self, all_events, event_store: EventStore):
        self.all_events = all_events
        self.event_store = event_store

    def has_not_event(self, stream_id: str, event_type: type[DomainEvent]):
        events = self.event_store.get_events(
            stream_id=stream_id,
            event_type=event_type
        )
        return len(events) == 0
    
    def has_event(self, stream_id: str, event_type: type[DomainEvent]):
        events = self.event_store.get_events(
            stream_id=stream_id,
            event_type=event_type
        )
        return len(events) > 0

    def has_event_n(self, stream_id: str, event_type: type[DomainEvent], n: int):
        events = self.event_store.get_events(
            stream_id=stream_id,
            event_type=event_type
        )
        return len(events) == n

    def has_event_once(self, stream_id: str, event_type: type[DomainEvent]):
        return self.has_event_n(stream_id, event_type, 1)

    def has_event_with(self, stream_id: str, event_type: type[DomainEvent], **kwargs):
        events = self.event_store.get_events(
            stream_id=stream_id,
            event_type=event_type
        )
        return any(
            True for e in events
            if all(e.__dict__.get(k) == v for k,v in kwargs.items())
        )

    def assert_has_not_event(self, stream_id: str, event_type: type[DomainEvent]):
        try:
            assert self.has_not_event(stream_id, event_type)
        except AssertionError:
            self.raise_error(f'event found: stream_id {stream_id} and topic {event_type.__name__}')

    def assert_has_event(self, stream_id: str, event_type: type[DomainEvent]):
        try:
            assert self.has_event(stream_id, event_type)
        except AssertionError:
            self.raise_error(f'event not found: stream_id {stream_id} and topic {event_type.__name__}')

    def assert_has_event_n(self, stream_id: str, event_type: type[DomainEvent], n: int):
        try:
            assert self.has_event_n(stream_id, event_type, n)
        except AssertionError:
            self.raise_error(f'event not found {n} times: stream_id {stream_id} and topic {event_type.__name__}')

    def assert_has_event_once(self, stream_id: str, event_type: type[DomainEvent]):
        try:
            assert self.has_event_once(stream_id, event_type)
        except AssertionError:
            self.raise_error(f'event not found once: stream_id {stream_id} and topic {event_type.__name__}')

    def assert_has_event_with(self, stream_id: str, event_type: type[DomainEvent], **kwargs):
        try:
            assert self.has_event_with(stream_id, event_type, **kwargs)
        except AssertionError:
            self.raise_error(f'event not found: stream_id {stream_id} and topic {event_type.__name__} and {json.dumps(kwargs)}')

    def raise_error(self, message):
        tb = None
        depth = 2

        while True:
            try:
                frame = sys._getframe(depth)
            except ValueError:
                break

            tb = types.TracebackType(tb, frame, frame.f_lasti, frame.f_lineno)
            depth += 1
        
        events = '\n' + '\n'.join(str(e) for e in self.all_events)

        raise AssertionError(f'{message}\n\nAll events: {str(events)}').with_traceback(tb)


class IntegrationEventsTestExpression:

    def __init__(self, integration_events):
        self.integration_events = integration_events

    def has_not_integration(self, integration_type: type[IntegrationEvent]):
        integrations = tuple([
            i for i in self.integration_events
            if isinstance(i, integration_type)
        ])
        return len(integrations) == 0

    def has_integration(self, integration_type: type[IntegrationEvent]):
        integrations = tuple([
            i for i in self.integration_events
            if isinstance(i, integration_type)
        ])
        return len(integrations) == 1

    def has_integration_with(self, integration_type: type[IntegrationEvent], **kwargs):
        integrations = tuple([
            True for i in self.integration_events
            if isinstance(i, integration_type)
            and all(i.__dict__.get(k) == v for k,v in kwargs.items())
        ])
        return len(integrations) == 1

    def assert_has_not_integration(self, integration_type: type[IntegrationEvent]):
        try:
            assert self.has_not_integration(integration_type)
        except AssertionError:
            topic = integration_type.__name__
            self.raise_error(f'integration event found: topic {topic}')

    def assert_has_integration(self, integration_type: type[IntegrationEvent]):
        try:
            assert self.has_integration(integration_type)
        except AssertionError:
            topic = integration_type.__name__
            self.raise_error(f'integration not found: topic {topic}')

    def assert_has_integration_with(self, integration_type: type[IntegrationEvent], **kwargs):
        try:
            assert self.has_integration_with(integration_type, **kwargs)
        except AssertionError:
            topic = integration_type.__name__
            self.raise_error(f'integration not found: {topic} and {json.dumps(kwargs)}')

    def raise_error(self, message):
        tb = None
        depth = 2

        while True:
            try:
                frame = sys._getframe(depth)
            except ValueError:
                break

            tb = types.TracebackType(tb, frame, frame.f_lasti, frame.f_lineno)
            depth += 1
        
        integrations = '\n' + '\n'.join(str(i) for i in self.integration_events)

        raise AssertionError(f'{message}\n\nAll records: {str(integrations)}').with_traceback(tb)