from __future__ import annotations

import typing
import dataclasses

from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import Identity
from domainpy.domain.repository import IRepository, TAggregateRoot, TIdentity
from domainpy.infrastructure.eventsourced.eventstream import EventStream
from domainpy.utils.bus import Bus, ISubscriber

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.infrastructure.eventsourced.eventstore import EventStore


@dataclasses.dataclass
class SnapshotConfiguration:
    enabled: bool
    every_n_events: typing.Optional[int] = None
    when_store_event: typing.Optional[typing.Type[DomainEvent]] = None


def make_adapter(
    aggregate_root_type: typing.Type[TAggregateRoot],
    identity_type: typing.Type[TIdentity],
):
    class EventSourcedRepositoryAdapter(
        IRepository[TAggregateRoot, TIdentity]
    ):
        def __init__(
            self,
            event_store: EventStore,
            *,
            snapshot_configuration: SnapshotConfiguration = None,
        ) -> None:
            self.event_store = event_store

            if snapshot_configuration is not None:
                self.snapshot_configuration = snapshot_configuration
            else:
                self.snapshot_configuration = SnapshotConfiguration(
                    enabled=False
                )

            self.event_bus = Bus[DomainEvent]()

        def attach(self, subscriber: ISubscriber) -> None:
            self.event_bus.attach(subscriber)

        def save(self, aggregate: TAggregateRoot) -> None:
            events = EventStream(aggregate.__changes__)
            self.event_store.store_events(events)

            if self._should_take_snapshot(aggregate):
                snapshot = self._take_snapshot(aggregate)
                self.event_store.store_events(EventStream([snapshot]))

            for event in events:
                self.event_bus.publish(event)

        def get(
            self, identity: typing.Union[TIdentity, str]
        ) -> typing.Optional[TAggregateRoot]:
            if isinstance(identity, str):
                identity = identity_type.from_text(identity)

            aggregate = aggregate_root_type(typing.cast(Identity, identity))

            if self._is_snapshot_enabled():
                snapshot_stream_id = aggregate.create_snapshot_stream_id(
                    identity
                )
                snapshot = self._get_stored_snapshot(snapshot_stream_id)
                if snapshot is not None:
                    aggregate.__route__(snapshot, is_snapshot=True)

            from_number = None
            if aggregate.__version__ > 0:
                from_number = aggregate.__version__ + 1

            stream_id = aggregate.create_stream_id(identity)
            events = self.event_store.get_events(
                stream_id,
                from_number=from_number,
            )

            for event in events:
                aggregate.__route__(event)

            if aggregate.__version__ == 0:
                return None

            return aggregate

        def _is_snapshot_enabled(self):
            return self.snapshot_configuration.enabled

        def _should_take_snapshot(self, aggregate: TAggregateRoot) -> bool:
            if self.snapshot_configuration.enabled:
                every_n_events = self.snapshot_configuration.every_n_events
                if every_n_events is not None:
                    return len(aggregate.__seen__) >= every_n_events

                when_store_event = self.snapshot_configuration.when_store_event
                if when_store_event is not None:
                    return len(aggregate.__changes__) >= 1 and isinstance(
                        aggregate.__changes__[-1], when_store_event
                    )

            return False

        def _get_stored_snapshot(
            self, snapshot_stream_id: str
        ) -> typing.Optional[DomainEvent]:
            snapshots = self.event_store.get_events(snapshot_stream_id)

            if len(snapshots) == 0:
                return None

            return snapshots[-1]

        @classmethod
        def _take_snapshot(cls, aggregate: TAggregateRoot) -> DomainEvent:
            return aggregate.take_snapshot()

    return EventSourcedRepositoryAdapter
