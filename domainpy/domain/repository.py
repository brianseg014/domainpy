import typing

TAggregateRoot = typing.TypeVar("TAggregateRoot")
TIdentity = typing.TypeVar("TIdentity")


class IRepository(typing.Generic[TAggregateRoot, TIdentity]):
    def save(self, aggregate: TAggregateRoot):
        raise NotImplementedError(
            f"{self.__class__.__name__} should override save method"
        )

    def get(self, identity: typing.Union[TIdentity, str]) -> TAggregateRoot:
        raise NotImplementedError(
            f"{self.__class__.__name__} should override save method"
        )
