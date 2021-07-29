from __future__ import annotations

import typing

from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.value_object import Identity
from domainpy.domain.repository import IRepository

if typing.TYPE_CHECKING:
    from domainpy.infrastructure.eventsourced.eventstore import EventStore


def make_adapter(
    aggregate_root_type: typing.Type[AggregateRoot],
    identity_type: typing.Type[Identity],
):
    class EventSourcedRepositoryAdapter(IRepository):
        def __init__(self, event_store: EventStore) -> None:
            self.event_store = event_store

        def save(self, aggregate) -> None:
            self.event_store.store_events(aggregate.__changes__)

        def get(self, identity):
            if isinstance(identity, str):
                identity = identity_type.from_text(identity)

            events = self.event_store.get_events(
                f"{identity.identity}:{aggregate_root_type.__name__}"
            )

            if len(events) == 0:
                return None

            aggregate = aggregate_root_type(identity)
            for event in events:
                aggregate.__route__(event)

            return aggregate

    return EventSourcedRepositoryAdapter
