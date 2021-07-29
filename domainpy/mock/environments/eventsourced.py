from __future__ import annotations

import sys
import uuid
import types
import typing
import datetime
import functools
import dataclasses


from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.event import DomainEvent
from domainpy.environments.eventsourced import EventSourcedEnvironment
from domainpy.infrastructure.eventsourced.eventstream import EventStream
from domainpy.infrastructure.eventsourced.recordmanager import (
    EventRecordManager,
)
from domainpy.infrastructure.eventsourced.managers.memory import (
    MemoryEventRecordManager,
)
from domainpy.infrastructure.publishers.memory import MemoryPublisher
from domainpy.infrastructure.mappers import Mapper
from domainpy.utils.bus_adapters import PublisherBusAdapter
from domainpy.utils.traceable import Traceable

if typing.TYPE_CHECKING:
    from domainpy.typing.application import SystemMessage  # type: ignore


@dataclasses.dataclass(frozen=True)
class Then:
    domain_events: DomeinEventsTestExpression
    integration_events: IntegrationEventsTestExpression


class EventSourcedEnvironmentTestAdapter(EventSourcedEnvironment):
    def __init__(self, *args, **kwargs) -> None:
        self.domain_events = MemoryPublisher()
        self.integration_events = MemoryPublisher()
        super().__init__(*args, **kwargs)

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
        domain_publisher_bus.attach(self.domain_events)

    def setup_integration_publisher_bus(
        self,
        integration_publisher_bus: PublisherBusAdapter[IntegrationEvent],
        integration_mapper: Mapper,
        setupargs: dict,
    ) -> None:
        integration_publisher_bus.attach(self.integration_events)

    @classmethod
    def stamp_command(
        cls,
        command_type: typing.Type[ApplicationCommand],
        *,
        trace_id: str = None,
    ):
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        return functools.partial(
            command_type,
            __trace_id__=trace_id,
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
        )

    @classmethod
    def stamp_integration(
        cls,
        integration_type: typing.Type[IntegrationEvent],
        *,
        trace_id: str = None,
    ):
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        return functools.partial(
            integration_type,
            __trace_id__=trace_id,
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
        )

    def stamp_event(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot],
        aggregate_id: str = None,
        *,
        trace_id: str = None,
    ):
        if aggregate_id is None:
            aggregate_id = str(uuid.uuid4())

        if trace_id is None:
            trace_id = str(uuid.uuid4())

        events = self.event_store.get_events(
            f"{aggregate_id}:{aggregate_type.__name__}"
        )

        return functools.partial(
            event_type,
            __trace_id__=trace_id,
            __stream_id__=f"{aggregate_id}:{aggregate_type.__name__}",
            __number__=len(events) + 1,
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
        )

    def given(self, event: DomainEvent):
        Traceable.__trace_id__ = event.__trace_id__
        self.event_store.store_events(EventStream([event]))

    def when(self, message: SystemMessage):
        self.handle(message)

    @property
    def then(self):
        return Then(
            domain_events=DomeinEventsTestExpression(self.domain_events),
            integration_events=IntegrationEventsTestExpression(
                self.integration_events
            ),
        )


TDomainEvent = typing.TypeVar("TDomainEvent", bound=DomainEvent)


class DomeinEventsTestExpression:
    def __init__(self, domain_events: typing.List[DomainEvent]):
        self.domain_events = domain_events

    @classmethod
    def get_stream_id(
        cls, aggregate_type: typing.Type[AggregateRoot], aggregate_id: str
    ) -> str:
        return f"{aggregate_id}:{aggregate_type.__name__}"

    def get_events(
        self,
        event_type: typing.Type[TDomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
    ) -> typing.Generator[TDomainEvent, None, None]:
        events = (e for e in self.domain_events if isinstance(e, event_type))
        if aggregate_type is not None or aggregate_id is not None:
            if aggregate_type is None or aggregate_id is None:
                raise AttributeError(
                    "both aggregate_type and aggregate_id should be set"
                )

            stream_id = self.get_stream_id(aggregate_type, aggregate_id)
            events = (  # type: ignore
                e
                for e in events
                if e.__stream_id__ == stream_id  # type: ignore
            )
        return events

    def has_not_event(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
    ) -> bool:
        events = self.get_events(event_type, aggregate_type, aggregate_id)
        return len(list(events)) == 0

    def has_event(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
    ) -> bool:
        events = self.get_events(event_type, aggregate_type, aggregate_id)
        return len(list(events)) > 0

    def has_event_n_times(
        self,
        event_type: typing.Type[DomainEvent],
        times: int,
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
    ) -> bool:
        events = self.get_events(event_type, aggregate_type, aggregate_id)
        return len(list(events)) == times

    def has_event_once(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
    ) -> bool:
        return self.has_event_n_times(
            event_type, 1, aggregate_type, aggregate_id
        )

    def has_event_with(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
        **kwargs,
    ) -> bool:
        events = self.get_events(event_type, aggregate_type, aggregate_id)
        return any(
            True
            for e in events
            if all(e.__dict__.get(k) == v for k, v in kwargs.items())
        )

    def has_not_event_with(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
        **kwargs,
    ) -> bool:
        return not self.has_event_with(
            event_type, aggregate_type, aggregate_id, **kwargs
        )

    def assert_has_not_event(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
    ) -> None:
        try:
            assert self.has_not_event(event_type, aggregate_type, aggregate_id)
        except AssertionError:
            self.raise_error("event found")

    def assert_has_event(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
    ) -> None:
        try:
            assert self.has_event(event_type, aggregate_type, aggregate_id)
        except AssertionError:
            self.raise_error("event not found")

    def assert_has_event_n_times(
        self,
        event_type: typing.Type[DomainEvent],
        times: int,
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
    ) -> None:
        try:
            assert self.has_event_n_times(
                event_type, times, aggregate_type, aggregate_id
            )
        except AssertionError:
            self.raise_error(f"event not found {times} time(s)")

    def assert_has_event_once(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
    ) -> None:
        try:
            assert self.has_event_once(
                event_type, aggregate_type, aggregate_id
            )
        except AssertionError:
            self.raise_error("event not found 1 time")

    def assert_has_event_with(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
        **kwargs,
    ) -> None:
        try:
            assert self.has_event_with(
                event_type, aggregate_type, aggregate_id, **kwargs
            )
        except AssertionError:
            self.raise_error("event not found")

    def assert_has_not_event_with(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot] = None,
        aggregate_id: str = None,
        **kwargs,
    ) -> None:
        try:
            assert self.has_not_event_with(
                event_type,
                aggregate_type,
                aggregate_id,
                **kwargs,
            )
        except AssertionError:
            self.raise_error("event found")

    def raise_error(self, message):
        traceback = None
        depth = 2

        while True:
            try:
                frame = sys._getframe(  # pylint: disable=protected-access
                    depth
                )
            except ValueError:
                break

            traceback = types.TracebackType(
                traceback, frame, frame.f_lasti, frame.f_lineno
            )
            depth += 1

        events = "\n" + "\n".join(str(e) for e in self.domain_events)

        raise AssertionError(
            f"{message}\n\nAll events: {str(events)}"
        ).with_traceback(traceback)


class IntegrationEventsTestExpression:
    def __init__(
        self, integration_events: typing.Tuple[IntegrationEvent, ...]
    ):
        self.integration_events = integration_events

    def get_integrations(
        self, integration_type: typing.Type[IntegrationEvent]
    ) -> typing.Generator[IntegrationEvent, None, None]:
        integrations = (
            i
            for i in self.integration_events
            if isinstance(i, integration_type)
        )
        return integrations

    def has_not_integration(
        self, integration_type: typing.Type[IntegrationEvent]
    ) -> bool:
        integrations = self.get_integrations(integration_type)
        return len(list(integrations)) == 0

    def has_integration(
        self, integration_type: typing.Type[IntegrationEvent]
    ) -> bool:
        integrations = self.get_integrations(integration_type)
        return len(list(integrations)) >= 1

    def has_integration_with(
        self, integration_type: typing.Type[IntegrationEvent], **kwargs
    ) -> bool:
        integrations = self.get_integrations(integration_type)
        return any(
            True
            for i in integrations
            if all(i.__dict__.get(k) == v for k, v in kwargs.items())
        )

    def has_not_integration_with(
        self, integration_type: typing.Type[IntegrationEvent], **kwargs
    ) -> bool:
        return not self.has_integration_with(integration_type, **kwargs)

    def assert_has_not_integration(
        self, integration_type: typing.Type[IntegrationEvent]
    ) -> None:
        try:
            assert self.has_not_integration(integration_type)
        except AssertionError:
            self.raise_error("integration event found")

    def assert_has_integration(
        self, integration_type: typing.Type[IntegrationEvent]
    ) -> None:
        try:
            assert self.has_integration(integration_type)
        except AssertionError:
            self.raise_error("integration not found")

    def assert_has_integration_with(
        self, integration_type: typing.Type[IntegrationEvent], **kwargs
    ) -> None:
        try:
            assert self.has_integration_with(integration_type, **kwargs)
        except AssertionError:
            self.raise_error("integration not found")

    def assert_has_not_integration_with(
        self, integration_type: typing.Type[IntegrationEvent], **kwargs
    ) -> None:
        try:
            assert self.has_not_integration_with(integration_type, **kwargs)
        except AssertionError:
            self.raise_error("integration found")

    def raise_error(self, message):
        traceback = None
        depth = 2

        while True:
            try:
                frame = sys._getframe(  # pylint: disable=protected-access
                    depth
                )
            except ValueError:
                break

            traceback = types.TracebackType(
                traceback, frame, frame.f_lasti, frame.f_lineno
            )
            depth += 1

        integrations = "\n" + "\n".join(
            str(i) for i in self.integration_events
        )

        raise AssertionError(
            f"{message}\n\nAll records: {str(integrations)}"
        ).with_traceback(traceback)
