
from domainpy.exceptions import DefinitionError
import typing
import collections.abc


T = typing.TypeVar('T')

class ISubscriber(typing.Generic[T]):

    def __route__(self, message: T):
        raise NotImplementedError(f'__route__ must be override in {self.__class__.__name__}')


class IBus(typing.Generic[T]):

    def attach(self, subsciber: ISubscriber[T]):
        pass

    def publish(self, message: T):
        pass

class Bus(IBus[T], ISubscriber[T]):

    def __init__(self, publish_exceptions: typing.Union[Exception, typing.Sequence[Exception]] = []):
        if not isinstance(publish_exceptions, collections.abc.Sequence):
            publish_exceptions = tuple([publish_exceptions])

        self.publish_exceptions = publish_exceptions

        self.subscribers = list[ISubscriber[T]]()

    def __route__(self, message: T):
        self.publish(message)

    def attach(self, subscriber: ISubscriber[T]):
        if not hasattr(subscriber, '__route__'):
            raise DefinitionError(f'{subscriber.__class__.__name__} should have __route__ method. Check bus_subscribers.')

        self.subscribers.append(subscriber)
    
    def publish(self, message: T):
        exceptions = []

        for s in self.subscribers:

            try:
                s.__route__(message)
            except Exception as e:
                if len(self.publish_exceptions) > 0 and isinstance(e, self.publish_exceptions):
                    exceptions.append(e)
                else:
                    raise e
        for e in exceptions:
            self.publish(e)