
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
        
    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)
        
    def __call__(self, service, message):
        if not self._has_any_handler(service, message):
            return

        if hasattr(message, '__trace_id__'):
            Traceable.__trace_id__ = message.__trace_id__
        else:
            Traceable.__trace_id__ = None

        results = [self.func(service, message)]
        
        handlers = self._handlers.get(message.__class__, set())
        for h in handlers:
            results.append(h(service, message))

        if(hasattr(service, '__partials__')):
            partials = service.__partials__.get(message.__class__, set())
            for h in set(partials):
                results.append(h(service, message))
                partials.remove(h)

        return results

    def _has_any_handler(self, service, message):
        if (message.__class__ in self._handlers):
            return True

        if (hasattr(service, '__partials__') and message.__class__ in service.__partials__):
            return True

        return False
        
            
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

    def trace(self, *messages):
        def inner_function(func):
            def wrapper(*args, **kwargs):
                service = args[0]
                trace = kwargs.pop('__trace__')
                leadings = kwargs.pop('__leadings__')

                if(not hasattr(service, '__partials__')):
                    service.__partials__ = dict()

                if len(leadings) > 0:
                    new_trace = []
                    new_trace.extend(trace)
                    new_trace.append(args[1])

                    service.__partials__.setdefault(leadings[0], set()).add(partial(wrapper, __trace__=new_trace, __leadings__=leadings[1:]))
                else:
                    return func(service, *trace, *args[1:], **kwargs)

            self._handlers.setdefault(messages[0], set()).add(partial(wrapper, __trace__=[], __leadings__=messages[1:]))

            return wrapper

        return inner_function

    