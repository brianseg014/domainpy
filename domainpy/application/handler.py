
from functools import update_wrapper, partial

from domainpy.application.command import ApplicationCommand
from domainpy.application.service import ApplicationService
from domainpy.application.exceptions import (
    HandlerNotFoundError,
    MessageSingleHandlerBroken
)


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
            #raise HandlerNotFoundError((message.__class__.__name__ + " in " + service.__class__.__name__))
            return
        
        results = []
        
        handlers = self._messages.get(message.__class__, [])
        for h in handlers:
            results.append(h(service, message))
            
        return results
            
    def command(self, command_type: type):
        def inner_function(func):
            
            if command_type in self._messages:
                raise MessageSingleHandlerBroken(f'handler already defined for {command_type}')
                
            self._messages.setdefault(command_type, set()).add(func)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function
        
    def query(self, query_type: type):
        def inner_function(func):
            
            if query_type in self._messages:
                raise MessageSingleHandlerBroken(f'handler already defined for {query_type}')
            
            self._messages.setdefault(query_type, set()).add(func)
            
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
