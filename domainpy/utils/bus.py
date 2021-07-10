
import typing


T = typing.TypeVar('T')

class Subscriber(typing.Generic[T]):

    def __route__(self, message: T):
        raise NotImplementedError(f'__route__ must be override in {self.__class__.__name__}')


class BasicSubscriber(Subscriber[T], list):

    def __route__(self, message: T):
        self.append(message)


class Bus(typing.Generic[T]):

    def __init__(self):
        self.subscribers = []

    def __route__(self, message: T):
        self.publish(message)

    def attach(self, subscriber: Subscriber[T]):
        self.subscribers.append(subscriber)
    
    def publish(self, message: T):
        for s in self.subscribers:
            s.__route__(message)
