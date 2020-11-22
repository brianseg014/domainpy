
from functools import update_wrapper, partial

from domainpy.application.command import ApplicationCommand
from domainpy.application.service import ApplicationService


class handler:
    
    def __init__(self, func):
        update_wrapper(self, func)
        
        self.func = func
        
        self._handables = dict()
        
    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)
        
    def __call__(self, service, handable):
        handlers = self._handables.get(handable.__class__, [])
        
        for h in handlers:
            h(service, handable)
        
    def command(self, command_type: type):
        def inner_function(func):
            
            self._handables.setdefault(command_type, set()).add(func)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function
        
    def event(self, event_type: type):
        def inner_function(func):
            
            self._handables.setdefault(event_type, set()).add(func)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function
