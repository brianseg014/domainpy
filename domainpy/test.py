import sys
import types
import json
import itertools
import datetime
import collections
import typing
import functools

from domainpy.typing import SystemMessage
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.mappers import EventMapper
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.managers.memory import MemoryEventRecordManager
from domainpy.utils.bus import Bus, BasicSubscriber
from domainpy.utils.registry import Registry


class Setup(typing.Protocol):
    def __call__(self, 
            registry: Registry, 
            handler_bus: Bus[SystemMessage], 
            resolver_bus: Bus[SystemMessage], 
            integration_bus: Bus[SystemMessage]):
        pass


Then = collections.namedtuple('Then', ('event_store', 'integration_events'))

class Environment:

    def __init__(self, event_mapper: EventMapper):
        self.event_mapper = event_mapper

    def setup(self, func: Setup):

        @functools.wraps(func)
        def wapper(*args, **kwargs):
            self.sequences = {}

            self.event_store_bus = Bus[DomainEvent]()
            self.event_record_manager = MemoryEventRecordManager()
            self.event_store = EventStore(
                event_mapper=self.event_mapper, 
                record_manager=self.event_record_manager,
                bus=self.event_store_bus
            )

            self.registry = Registry()

            self.resolver_bus = Bus[SystemMessage]()
            self.event_store_bus.attach(self.resolver_bus)

            self.handler_bus = Bus[SystemMessage]()
            self.event_subscriber = BasicSubscriber[DomainEvent]()
            self.event_store_bus.attach(self.event_subscriber)
            self.event_store_bus.attach(self.handler_bus)

            self.integration_bus = Bus[SystemMessage]()
            self.integration_subscriber = BasicSubscriber[SystemMessage]()
            self.integration_bus.attach(self.integration_subscriber)

            func(self.registry, self.handler_bus, self.resolver_bus, self.integration_bus)
        
        return wapper

    def tear_down(self):
        self.sequences = {}

        self.event_record_manager.clear()
        self.integration_subscriber.clear()

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
            event_store=EventStoreTestExpression(self.event_subscriber, self.event_store),
            integration_events=IntegrationEventsTestExpression(self.integration_subscriber)
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
        try:
            assert len(events) == 0
        except AssertionError:
            self.raise_error(f'event found: stream_id {stream_id} and topic {event_type.__name__}')
    
    def has_event(self, stream_id: str, event_type: type[DomainEvent]):
        events = self.event_store.get_events(
            stream_id=stream_id,
            event_type=event_type
        )
        try:
            assert len(events) > 0
        except AssertionError:
            self.raise_error(f'event not found: stream_id {stream_id} and topic {event_type.__name__}')

    def has_event_once(self, stream_id: str, event_type: type[DomainEvent]):
        events = self.event_store.get_events(
            stream_id=stream_id,
            event_type=event_type
        )
        try:
            assert len(events) == 1
        except AssertionError:
            self.raise_error(f'event not found once: stream_id {stream_id} and topic {event_type.__name__}')

    def has_event_n(self, stream_id: str, event_type: type[DomainEvent], n: int):
        events = self.event_store.get_events(
            stream_id=stream_id,
            event_type=event_type
        )
        try:
            assert len(events) == n
        except AssertionError:
            self.raise_error(f'event not found {n} times: stream_id {stream_id} and topic {event_type.__name__}')

    def has_event_with(self, stream_id: str, event_type: type[DomainEvent], **kwargs):
        events = self.event_store.get_events(
            stream_id=stream_id,
            event_type=event_type
        )
        try:
            assert any(
                True for e in events
                if all(e.__dict__.get(k) == v for k,v in kwargs.items())
            )
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
        try:
            assert len(integrations) == 0
        except AssertionError:
            topic = integration_type.__name__
            self.raise_error(f'integration event found: topic {topic}')

    def has_integration(self, integration_type: type[IntegrationEvent]):
        integrations = tuple([
            i for i in self.integration_events
            if isinstance(i, integration_type)
        ])
        try:
            assert len(integrations) == 1
        except AssertionError:
            topic = integration_type.__name__
            self.raise_error(f'integration not found: topic {topic}')

    def has_integration_with(self, integration_type: type[IntegrationEvent], **kwargs):
        integrations = tuple([
            True for i in self.integration_events
            if isinstance(i, integration_type)
            and all(i.__dict__.get(k) == v for k,v in kwargs.items())
        ])
        try:
            assert len(integrations) == 1
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