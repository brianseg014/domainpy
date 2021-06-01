
from functools import update_wrapper, partial

from domainpy.application.command import ApplicationCommand
from domainpy.application.service import ApplicationService
from domainpy.application.exceptions import (
    HandlerNotFoundError,
    MessageSingleHandlerBroken
)
from domainpy.utils.traceable import Traceable


class handler:
    
    def __init__(self, func):
        update_wrapper(self, func)
        
        self.func = func
        
        self._handlers = dict()
        self._partials = dict()
        
    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)
        
    def __call__(self, service, message):
        if (message.__class__ not in self._handlers 
                and message.__class__ not in self._partials):
            return

        if hasattr(message, '__trace_id__'):
            Traceable.__trace_id__ = message.__trace_id__
        else:
            Traceable.__trace_id__ = None

        results = [self.func(service, message)]
        
        handlers = self._handlers.get(message.__class__, set())
        for h in handlers:
            results.append(h(service, message))

        partials = self._partials.get(message.__class__, set())
        for h in set(partials):
            results.append(h(service, message))
            partials.remove(h)

        return results
            
    def command(self, command_type: type):
        def inner_function(func):
            
            if command_type in self._handlers:
                raise MessageSingleHandlerBroken(f'handler already defined for {command_type}')
                
            self._handlers.setdefault(command_type, set()).add(func)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function

    def integration(self, integration_type: type):
        def inner_function(func):
            
            self._handlers.setdefault(integration_type, set()).add(func)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function
        
    def query(self, query_type: type):
        def inner_function(func):
            
            if query_type in self._handlers:
                raise MessageSingleHandlerBroken(f'handler already defined for {query_type}')
            
            self._handlers.setdefault(query_type, set()).add(func)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function
        
    def event(self, event_type: type):
        def inner_function(func):
            
            self._handlers.setdefault(event_type, set()).add(func)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner_function

    def event_trace(self, *events):
        def inner_function(func):

            def wrapper(*args, **kwargs):
                trace = kwargs.pop('trace')
                leadings = kwargs.pop('leadings')

                if len(leadings) > 0:
                    trace.append(args[1])

                    self._partials.setdefault(leadings[0], set()).add(partial(wrapper, trace=trace, leadings=leadings[1:]))
                else:
                    return func(args[0], *trace, *args[1:], **kwargs)

            self._handlers.setdefault(events[0], set()).add(partial(wrapper, trace=[], leadings=events[1:]))

            return wrapper

        return inner_function