
import typing


T = typing.TypeVar('T')

class ISubscriber(typing.Generic[T]):

    def __route__(self, message: T):
        raise NotImplementedError(f'__route__ must be override in {self.__class__.__name__}')


class BasicSubscriber(ISubscriber[T], list):

    def __route__(self, message: T):
        self.append(message)


class IBus(typing.Generic[T]):

    def attach(self, subsciber: ISubscriber[T]):
        pass

    def publish(self, message: T):
        pass

class Bus(IBus[T], ISubscriber[T]):

    def __init__(self):
        self.subscribers = list[ISubscriber[T]]()

    def __route__(self, message: T):
        self.publish(message)

    def attach(self, subscriber: ISubscriber[T]):
        self.subscribers.append(subscriber)
    
    def publish(self, message: T):
        for s in self.subscribers:
            s.__route__(message)
