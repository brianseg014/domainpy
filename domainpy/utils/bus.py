import abc
import typing

from domainpy.exceptions import DefinitionError

Message = typing.TypeVar("Message")


class ISubscriber(typing.Generic[Message], abc.ABC):
    @abc.abstractmethod
    def __route__(self, message: Message) -> None:
        pass  # pragma: no cover


class IBus(typing.Generic[Message], abc.ABC):
    @abc.abstractmethod
    def attach(self, subscriber: ISubscriber[Message]) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def publish(self, message: Message) -> None:
        pass  # pragma: no cover


class Bus(IBus[Message]):
    def __init__(self):
        self.subscribers: typing.List[ISubscriber[Message]] = []

    def attach(self, subscriber: ISubscriber[Message]) -> None:
        if not hasattr(subscriber, "__route__"):
            sub_name = subscriber.__class__.__name__
            raise DefinitionError(
                f"{sub_name} should have __route__ method. "
                "Check bus_subscribers."
            )

        self.subscribers.append(subscriber)

    def publish(self, message: Message) -> None:
        for subscriber in self.subscribers:
            subscriber.__route__(message)
