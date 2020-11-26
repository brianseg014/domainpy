
from functools import update_wrapper, partial

from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.exceptions import MutatorNotFoundError

class mutator:
    
    def __init__(self, func):
        update_wrapper(self, func)
        
        self.func = func
        
        self._events = dict()
        
    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)
        
    def __call__(self, aggregate, event: DomainEvent):
        if(event.__class__ not in self._events):
            raise MutatorNotFoundError(event.__class__.__name__ + " in " + aggregate.__class__.__name__)
        
        mutators = self._events[event.__class__]
        for m in mutators:
            m(aggregate, event)
        
    def event(self, event_type: type):
        def inner_function(func):
            
            self._events.setdefault(event_type, set()).add(func)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function