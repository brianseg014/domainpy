from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from domainpy.domain.model.aggregate import AggregateRoot
    from domainpy.domain.model.event import DomainEvent

from domainpy.domain.model.value_object import Identity
from domainpy.exceptions import DefinitionError


class DomainEntity:
    def __init__(self, id: Identity, aggregate: AggregateRoot):
        self.__id__ = id
        self.__aggregate__ = aggregate

    def __apply__(self, event: DomainEvent):
        self.__aggregate__.__apply__(event)

    def __route__(self, event: DomainEvent):
        self.mutate(event)

    def __eq__(self, other: typing.Union["DomainEntity", Identity]):
        if other is None:
            return False

        if isinstance(other, DomainEntity):
            return self.__id__ == other.__id__
        elif isinstance(other, Identity):
            return self.__id__ == other
        else:
            self_name = self.__class__.__name__
            other_name = other.__class__.__name__
            raise DefinitionError(
                f"cannot compare {self_name} with {other_name}"
            )

    def __repr__(self):
        self_name = self.__class__.__name__
        self_id = self.__id__
        return f"{self_name}(id={self_id})"  # pragma: no cover

    def mutate(self, event: "DomainEvent"):
        pass  # pragma: no cover
