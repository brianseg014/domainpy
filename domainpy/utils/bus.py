import typing

from domainpy.exceptions import DefinitionError

T = typing.TypeVar("T")


class ISubscriber(typing.Generic[T]):
    def __route__(self, message: T):
        raise NotImplementedError(
            f"__route__ must be override in {self.__class__.__name__}"
        )


class IBus(typing.Generic[T]):
    def attach(self, subsciber: ISubscriber[T]):
        pass

    def publish(self, message: T):
        pass


class Bus(IBus[T]):
    def __init__(self):
        self.subscribers: typing.List[ISubscriber[T]] = []

    def attach(self, subscriber: ISubscriber[T]):
        if not hasattr(subscriber, "__route__"):
            sub_name = subscriber.__class__.__name__
            raise DefinitionError(
                f"{sub_name} should have __route__ method. "
                "Check bus_subscribers."
            )

        self.subscribers.append(subscriber)

    def publish(self, message: T):
        for s in self.subscribers:
            s.__route__(message)
