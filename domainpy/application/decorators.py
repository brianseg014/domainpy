
from functools import update_wrapper, partial

from domainpy.application.command import ApplicationCommand
from domainpy.application.service import ApplicationService
from domainpy.domain.model.exceptions import HandlerNotFoundError


class handler:
    
    def __init__(self, func):
        update_wrapper(self, func)
        
        self.func = func
        
        self._messages = dict()
        
    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)
        
    def __call__(self, service, message):
        if(message.__class__ not in self._messages):
            raise HandlerNotFoundError((message.__class__.__name__ + " in " + service.__class__.__name__))
        
        handlers = self._messages.get(message.__class__, [])
        for h in handlers:
            h(service, message)
        
    def command(self, command_type: type):
        def inner_function(func):
            
            self._messages.setdefault(command_type, set()).add(func)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function
        
    def event(self, event_type: type):
        def inner_function(func):
            
            self._messages.setdefault(event_type, set()).add(func)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function
