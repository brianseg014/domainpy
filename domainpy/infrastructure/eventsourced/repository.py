from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from domainpy.infrastructure.eventsourced.eventstore import EventStore

from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.value_object import Identity
from domainpy.domain.repository import IRepository


def make_adapter(
    AggregateRoot: type[AggregateRoot], Identity: type[Identity]
):
    class EventSourcedRepositoryAdapter(IRepository):
        def __init__(self, event_store: EventStore) -> None:
            self.event_store = event_store

        def save(self, aggregate) -> None:
            self.event_store.store_events(aggregate.__changes__)

        def get(self, id):
            if isinstance(id, str):
                id = Identity.from_text(id)

            events = self.event_store.get_events(
                f"{id.id}:{AggregateRoot.__name__}"
            )

            if len(events) == 0:
                return None

            aggregate = AggregateRoot(id)
            for e in events:
                aggregate.__route__(e)

            return aggregate

    return EventSourcedRepositoryAdapter
