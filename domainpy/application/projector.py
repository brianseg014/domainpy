from functools import update_wrapper, partial

from domainpy.domain.model.event import DomainEvent
from domainpy.domain.exceptions import (
    MutatorNotFoundError,
    SingleMutatorBrokenError
)

class projector:
    
    def __init__(self, func):
        update_wrapper(self, func)
        
        self.func = func
        
        self._events = dict()
        
    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)
        
    def __call__(self, projection, event: DomainEvent):
        if(event.__class__ not in self._events):
            raise MutatorNotFoundError(event.__class__.__name__ + " in " + projection.__class__.__name__)
        
        m = self._events[event.__class__]
        m(projection, event)
        
    def event(self, event_type: type):
        def inner_function(func):
            
            if event_type in self._events:
                raise SingleMutatorBrokenError(f'{event_type} mutator already registerd')
            
            self._events[event_type] = func
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function