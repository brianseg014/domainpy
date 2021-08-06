import abc
import typing

from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.value_object import Identity
from domainpy.utils.bus import ISubscriber

TAggregateRoot = typing.TypeVar("TAggregateRoot", bound=AggregateRoot)
TIdentity = typing.TypeVar("TIdentity", bound=Identity)


class IRepository(typing.Generic[TAggregateRoot, TIdentity], abc.ABC):
    @abc.abstractmethod
    def save(self, aggregate: TAggregateRoot) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def get(
        self, identity: typing.Union[TIdentity, str]
    ) -> typing.Optional[TAggregateRoot]:  # pragma: no cover
        pass

    @abc.abstractmethod
    def attach(self, subscriber: ISubscriber) -> None:
        pass
