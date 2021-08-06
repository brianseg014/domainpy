from __future__ import annotations

import abc
import sys
import types
import typing
import dataclasses

from domainpy.bootstrap import Environment
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.eventstream import EventStream
from domainpy.utils.traceable import Traceable
from domainpy.utils.bus_subscribers import BasicSubscriber
from domainpy.typing.application import SystemMessage


@dataclasses.dataclass(frozen=True)
class Then:
    domain_events: DomainEventsTestExpression
    integration_events: IntegrationEventsTestExpression


class EventProcessor(abc.ABC):
    @abc.abstractmethod
    def process(self, event: DomainEvent) -> None:
        pass

    def next_event_number(
        self, aggregate_type: typing.Type[AggregateRoot], aggregate_id: str
    ) -> int:
        pass


class EventSourcedProcessor(EventProcessor):
    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    def process(self, event: DomainEvent) -> None:
        Traceable.__trace_id__ = event.__trace_id__
        self.event_store.store_events(EventStream([event]))

    def next_event_number(
        self, aggregate_type: typing.Type[AggregateRoot], aggregate_id: str
    ) -> int:
        stream_id = aggregate_type.create_stream_id(aggregate_id)
        events = self.event_store.get_events(stream_id)
        return len(events) + 1


class TestEnvironment(abc.ABC):
    def __init__(
        self, environment: Environment, event_processor: EventProcessor
    ) -> None:
        self.environment = environment
        self.event_processor = event_processor

        self.domain_events = BasicSubscriber()
        self.environment.service_bus.event_bus.attach(self.domain_events)

        self.integration_events = BasicSubscriber()
        self.environment.integration_bus.attach(self.integration_events)

    def next_event_number(
        self, aggregate_type: typing.Type[AggregateRoot], aggregate_id: str
    ) -> int:
        return self.event_processor.next_event_number(
            aggregate_type, aggregate_id
        )

    @classmethod
    def stamp_command(cls, command_type: typing.Type[ApplicationCommand]):
        return command_type.stamp()

    @classmethod
    def stamp_integration(
        cls, integration_type: typing.Type[IntegrationEvent]
    ):
        return integration_type.stamp()

    def stamp_event(
        self,
        event_type: typing.Type[DomainEvent],
        aggregate_type: typing.Type[AggregateRoot],
        aggregate_id: str,
    ):
        return event_type.stamp(
            stream_id=aggregate_type.create_stream_id(aggregate_id),
            number=self.next_event_number(aggregate_type, aggregate_id),
        )

    def given(self, event: DomainEvent) -> None:
        self.event_processor.process(event)
        self.environment.service_bus.event_bus.publish(event)

    def when(self, message: SystemMessage) -> None:
        self.environment.handle(message)

    @property
    def then(self) -> Then:
        return Then(
            domain_events=DomainEventsTestExpression(
                tuple(self.domain_events)
            ),
            integration_events=IntegrationEventsTestExpression(
                tuple(self.integration_events)
            ),
        )


TDomainEvent = typing.TypeVar("TDomainEvent", bound=DomainEvent)


class DomainEventsTestExpression:
    def __init__(self, domain_events: typing.Tuple[DomainEvent, ...]):
        self.domain_events = domain_events

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

            stream_id = aggregate_type.create_stream_id(aggregate_id)
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


TIntegrationEvent = typing.TypeVar("TIntegrationEvent", bound=IntegrationEvent)


class IntegrationEventsTestExpression:
    def __init__(
        self, integration_events: typing.Tuple[IntegrationEvent, ...]
    ):
        self.integration_events = integration_events

    def get_integrations(
        self, integration_type: typing.Type[TIntegrationEvent]
    ) -> typing.Generator[TIntegrationEvent, None, None]:
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