import abc
import typing

TAggregateRoot = typing.TypeVar("TAggregateRoot")
TIdentity = typing.TypeVar("TIdentity")


class IRepository(typing.Generic[TAggregateRoot, TIdentity], abc.ABC):
    @abc.abstractmethod
    def save(self, aggregate: TAggregateRoot):  # pragma: no cover
        pass

    @abc.abstractmethod
    def get(
        self, identity: typing.Union[TIdentity, str]
    ) -> TAggregateRoot:  # pragma: no cover
        pass
