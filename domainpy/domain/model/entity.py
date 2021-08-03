from __future__ import annotations

import abc
import typing

from domainpy.domain.model.value_object import Identity, ValueObject

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.domain.model.aggregate import AggregateRoot
    from domainpy.domain.model.event import DomainEvent


class DomainEntity(abc.ABC):
    def __init__(self, identity: Identity, aggregate: AggregateRoot) -> None:
        self.__identity__ = identity
        self.__aggregate__ = aggregate

    def __stamp__(self, event_type: typing.Type[DomainEvent]):
        return self.__aggregate__.__stamp__(event_type)

    def __apply__(self, event: DomainEvent) -> None:
        self.__aggregate__.__apply__(event)

    def __route__(self, event: DomainEvent) -> None:
        self.mutate(event)

    def __eq__(self, other: object) -> bool:
        if not isinstance(
            other, (self.__class__, self.__identity__.__class__)
        ):
            return False

        if isinstance(other, self.__class__):
            return self.__identity__ == other.__identity__

        if isinstance(other, self.__identity__.__class__):
            return self.__identity__ == other

        return False

    def __repr__(self) -> str:  # pragma: no cover
        self_name = self.__class__.__name__
        self_id = self.__identity__
        return f"{self_name}(id={self_id})"

    @abc.abstractmethod
    def mutate(self, event: DomainEvent) -> None:
        pass  # pragma: no cover
