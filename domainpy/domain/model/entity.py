from __future__ import annotations

import abc
import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.domain.model.aggregate import AggregateRoot
    from domainpy.domain.model.event import DomainEvent

from domainpy.domain.model.value_object import Identity, ValueObject


class DomainEntity(abc.ABC):
    def __init__(self, id: Identity, aggregate: AggregateRoot) -> None:
        self.__id__ = id
        self.__aggregate__ = aggregate

    def __stamp__(self, event_type: typing.Type[DomainEvent]):
        return self.__aggregate__.__stamp__(event_type)

    def __apply__(self, event: DomainEvent) -> None:
        self.__aggregate__.__apply__(event)

    def __route__(self, event: DomainEvent) -> None:
        self.mutate(event)

    def __setattr__(self, name: str, value: typing.Any) -> None:
        is_system = name.startswith("__") or name == "mutate"
        is_domain_object = isinstance(value, (DomainEntity, ValueObject))

        if not is_system and not is_domain_object:
            raise TypeError(
                "should only be composed of entites and value objects"
            )

        return super().__setattr__(name, value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (self.__class__, self.__id__.__class__)):
            return False

        if isinstance(other, self.__class__):
            return self.__id__ == other.__id__
        elif isinstance(other, self.__id__.__class__):
            return self.__id__ == other

        return False

    def __ne__(self, o: object) -> bool:
        return not self == o

    def __repr__(self) -> str:  # pragma: no cover
        self_name = self.__class__.__name__
        self_id = self.__id__
        return f"{self_name}(id={self_id})"

    @abc.abstractmethod
    def mutate(self, event: DomainEvent) -> None:
        pass  # pragma: no cover
