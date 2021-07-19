from __future__ import annotations
from domainpy.utils.traceable import Traceable

import sys
import json
import uuid
import types
import typing
import datetime
import functools
import itertools
import dataclasses

if typing.TYPE_CHECKING:
    from domainpy.typing import SystemMessage

from domainpy.application import ApplicationCommand, IntegrationEvent
from domainpy.domain.model import AggregateRoot, DomainEvent
from domainpy.environments import EventSourcedEnvironment
from domainpy.infrastructure import (
    EventStream,
    EventRecordManager,
    Mapper,
    MemoryEventRecordManager,
    MemoryPublisher,
)
from domainpy.utils import PublisherBusAdapter


@dataclasses.dataclass(frozen=True)
class Then:
    domain_events: "DomeinEventsTestExpression"
    integration_events: "IntegrationEventsTestExpression"


class EventSourcedEnvironmentTestAdapter(EventSourcedEnvironment):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.sequences: dict[str, typing.Iterator[int]] = {}

    def setup_event_record_manager(
        self, setupargs: dict
    ) -> EventRecordManager:
        return MemoryEventRecordManager()

    def setup_domain_publisher_bus(
        self,
        domain_publisher_bus: PublisherBusAdapter[DomainEvent],
        event_mapper: Mapper,
        setupargs: dict,
    ) -> None:
        self.domain_events = MemoryPublisher()
        domain_publisher_bus.attach(self.domain_events)

    def setup_integration_publisher_bus(
        self,
        integration_publisher_bus: PublisherBusAdapter[IntegrationEvent],
        integration_mapper: Mapper,
        setupargs: dict,
    ) -> None:
        self.integration_events = MemoryPublisher()
        integration_publisher_bus.attach(self.integration_events)

    def stamp_command(
        self,
        command_type: type[ApplicationCommand],
        new_trace: bool = True,
        trace_id: str = None,
    ):
        if trace_id is not None:
            self.trace_id = trace_id
        elif new_trace:
            self.trace_id = str(uuid.uuid4())

        return functools.partial(
            command_type,
            __trace_id__=self.trace_id,
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
        )

    def stamp_integration(
        self,
        integration_type: type[IntegrationEvent]
    ):
        return functools.partial(
            integration_type,
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now())
        )

    def stamp_event(
        self,
        event_type: type[DomainEvent],
        aggregate_type: type[AggregateRoot],
        new_trace: bool = True,
        new_stream: bool = True,
        trace_id: str = None,
        aggregate_id: str = None,
    ):
        if trace_id is not None:
            self.trace_id = trace_id
        elif new_trace:
            self.trace_id = str(uuid.uuid4())

        if aggregate_id is not None:
            self.stream_id = f"{aggregate_id}:{aggregate_type.__name__}"
        elif new_stream:
            self.stream_id = f"{str(uuid.uuid4())}:{aggregate_type.__name__}"
        else:
            raise AttributeError('either aggregate id or new_stream should be set')

        sequence = self.sequences.setdefault(
            self.stream_id, itertools.count(start=1, step=1)
        )

        return functools.partial(
            event_type,
            __trace_id__=self.trace_id,
            __stream_id__=self.stream_id,
            __number__=next(sequence),
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
        )

    def given(self, event: DomainEvent):
        self.event_store.store_events(EventStream([event]))

    def when(self, message: SystemMessage):
        Traceable.__trace_id__ = str(uuid.uuid4())
        self.handle(message)

    @property
    def then(self):
        return Then(
            domain_events=DomeinEventsTestExpression(self.domain_events),
            integration_events=IntegrationEventsTestExpression(
                self.integration_events
            ),
        )


class DomeinEventsTestExpression:
    def __init__(self, domain_events: list[DomainEvent]):
        self.domain_events = domain_events

    def get_stream_id(self, aggregate_type: type[AggregateRoot], aggregate_id: str) -> str:
        return f'{aggregate_id}:{aggregate_type.__name__}'

    def get_events(
        self, 
        event_type: type[DomainEvent],
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None
    ) -> tuple[DomainEvent]:
        events = tuple(
            [e for e in self.domain_events if isinstance(e, event_type)]
        )
        if aggregate_type is not None or aggregate_id is not None:
            if aggregate_type is None or aggregate_id is None:
                raise AttributeError('both aggregate_type and aggregate_id should be set')

            stream_id = self.get_stream_id(aggregate_type, aggregate_id)
            events = tuple([e for e in events if e.__stream_id__ == stream_id])
        return events

    def has_not_event(
        self,
        event_type: type[DomainEvent],
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None
    ) -> bool:
        events = self.get_events(event_type, aggregate_type, aggregate_id)
        return len(events) == 0

    def has_event(
        self,
        event_type: type[DomainEvent],
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None
    ) -> bool:
        events = self.get_events(event_type, aggregate_type, aggregate_id)
        return len(events) > 0

    def has_event_n(
        self,
        event_type: type[DomainEvent],
        n: int,
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None
    ) -> bool:
        events = self.get_events(event_type, aggregate_type, aggregate_id)
        return len(events) == n

    def has_event_once(
        self,
        event_type: type[DomainEvent],
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None
    ):
        return self.has_event_n(event_type, 1, aggregate_type, aggregate_id)

    def has_event_with(
        self,
        event_type: type[DomainEvent],
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None,
        **kwargs
    ) -> bool:
        events = self.get_events(event_type, aggregate_type, aggregate_id)
        return any(
            True
            for e in events
            if all(e.__dict__.get(k) == v for k, v in kwargs.items())
        )

    def assert_has_not_event(
        self,
        event_type: type[DomainEvent],
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None,
    ):
        try:
            assert self.has_not_event(event_type, aggregate_type, aggregate_id)
        except AssertionError:
            self.raise_error("event found")

    def assert_has_event(
        self,
        event_type: type[DomainEvent],
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None,
    ):
        try:
            assert self.has_event(event_type, aggregate_type, aggregate_id)
        except AssertionError:
            self.raise_error("event not found")

    def assert_has_event_n(
        self,
        event_type: type[DomainEvent],
        n: int,
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None,
    ):
        try:
            assert self.has_event_n(event_type, n, aggregate_type, aggregate_id)
        except AssertionError:
            self.raise_error(f"event not found {n} time(s)")

    def assert_has_event_once(
        self,
        event_type: type[DomainEvent],
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None,
    ):
        try:
            assert self.has_event_once(event_type, aggregate_type, aggregate_id)
        except AssertionError:
            self.raise_error("event not found 1 time")

    def assert_has_event_with(
        self,
        event_type: type[DomainEvent],
        aggregate_type: type[AggregateRoot] = None,
        aggregate_id: str = None,
        **kwargs
    ):
        try:
            assert self.has_event_with(
                event_type, aggregate_type, aggregate_id, **kwargs
            )
        except AssertionError:
            self.raise_error("event not found")

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

        events = "\n" + "\n".join(str(e) for e in self.domain_events)

        raise AssertionError(
            f"{message}\n\nAll events: {str(events)}"
        ).with_traceback(tb)


class IntegrationEventsTestExpression:
    def __init__(self, integration_events):
        self.integration_events = integration_events

    def get_integrations(self, integration_type: type[IntegrationEvent]):
        integrations = tuple(
            [
                i
                for i in self.integration_events
                if isinstance(i, integration_type)
            ]
        )
        return integrations

    def has_not_integration(self, integration_type: type[IntegrationEvent]):
        integrations = self.get_integrations(integration_type)
        return len(integrations) == 0

    def has_integration(self, integration_type: type[IntegrationEvent]):
        integrations = self.get_integrations(integration_type)
        return len(integrations) == 1

    def has_integration_with(
        self, integration_type: type[IntegrationEvent], **kwargs
    ):
        integrations = self.get_integrations(integration_type)
        integrations = tuple(
            [
                i
                for i in integrations
                if all(i.__dict__.get(k) == v for k, v in kwargs.items())
            ]
        )
        return len(integrations) == 1

    def assert_has_not_integration(
        self, integration_type: type[IntegrationEvent]
    ):
        try:
            assert self.has_not_integration(integration_type)
        except AssertionError:
            topic = integration_type.__name__
            self.raise_error(f"integration event found: topic {topic}")

    def assert_has_integration(self, integration_type: type[IntegrationEvent]):
        try:
            assert self.has_integration(integration_type)
        except AssertionError:
            topic = integration_type.__name__
            self.raise_error(f"integration not found: topic {topic}")

    def assert_has_integration_with(
        self, integration_type: type[IntegrationEvent], **kwargs
    ):
        try:
            assert self.has_integration_with(integration_type, **kwargs)
        except AssertionError:
            topic = integration_type.__name__
            self.raise_error(
                f"integration not found: {topic} and {json.dumps(kwargs)}"
            )

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

        integrations = "\n" + "\n".join(
            str(i) for i in self.integration_events
        )

        raise AssertionError(
            f"{message}\n\nAll records: {str(integrations)}"
        ).with_traceback(tb)
