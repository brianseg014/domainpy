
from domainpy.exceptions import DefinitionError
from typing import Type
import typing
from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import Identity

class DomainEntity:

    def __init__(self, id: Identity, aggregate: AggregateRoot):
        self.__id__ = id
        self.__aggregate__ = aggregate

    def __apply__(self, event: DomainEvent):
        self.__aggregate__.__apply__(event)

    def __route__(self, event: DomainEvent):
        self.mutate(event)

    def __eq__(self, other: typing.Union['DomainEntity', Identity]):
        if other is None:
            return False
        
        if isinstance(other, DomainEntity):
            return self.__id__ == other.__id__
        elif isinstance(other, Identity):
            return self.__id__ == other
        else:
            raise DefinitionError(f'cannot compare {DomainEntity.__name__} with {other.__class__.__name__}')

    def __repr__(self):
        return f'{self.__class__.__name__}(id={self.__id__})' # pragma: no cover

    def mutate(self, event: DomainEvent):
        pass # pragma: no cover