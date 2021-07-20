import collections.abc
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
    def __init__(
        self,
        publish_exceptions: typing.Union[
            type[Exception], tuple[type[Exception], ...], tuple[()]
        ] = (),
    ):
        if not isinstance(publish_exceptions, collections.abc.Sequence):
            publish_exceptions = tuple([publish_exceptions])

        self.publish_exceptions = publish_exceptions

        self.subscribers = list[ISubscriber[T]]()

    def attach(self, subscriber: ISubscriber[T]):
        if not hasattr(subscriber, "__route__"):
            sub_name = subscriber.__class__.__name__
            raise DefinitionError(
                f"{sub_name} should have __route__ method. "
                "Check bus_subscribers."
            )

        self.subscribers.append(subscriber)

    def publish(self, message: T):
        exceptions = []

        for s in self.subscribers:

            try:
                s.__route__(message)
            except Exception as e:
                if len(self.publish_exceptions) > 0 and isinstance(
                    e, self.publish_exceptions
                ):
                    exceptions.append(e)
                else:
                    raise e
        for ex in exceptions:
            self.publish(ex)  # type: ignore
