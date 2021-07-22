from __future__ import annotations

import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.domain.model.aggregate import AggregateRoot
    from domainpy.domain.model.event import DomainEvent

from domainpy.domain.model.value_object import Identity


class DomainEntity:
    def __init__(self, id: Identity, aggregate: AggregateRoot) -> None:
        self.__id__ = id
        self.__aggregate__ = aggregate

    def __stamp__(self, event_type: typing.Type[DomainEvent]):
        return self.__aggregate__.__stamp__(event_type)

    def __apply__(self, event: DomainEvent) -> None:
        self.__aggregate__.__apply__(event)

    def __route__(self, event: DomainEvent) -> None:
        self.mutate(event)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (self.__class__, self.__id__.__class__)):
            return False

        if isinstance(other, self.__class__):
            return self.__id__ == other.__id__
        elif isinstance(other, self.__id__.__class__):
            return self.__id__ == other

        return False

    def __repr__(self) -> str:  # pragma: no cover
        self_name = self.__class__.__name__
        self_id = self.__id__
        return f"{self_name}(id={self_id})"

    def mutate(self, event: DomainEvent) -> None:
        pass  # pragma: no cover
