from time import time
from functools import update_wrapper, partial

from domainpy.exceptions import DefinitionError
from domainpy.domain.model.value_object import Identity
from domainpy.domain.model.event import DomainEvent


class AggregateRoot:

    def __init__(self, id: Identity):
        self.__id__ = id

        self.__version__ = 0
        self.__changes__ = [] # New events
        self.__seen__ = [] # Routed events (mutated)

    @property
    def __selector__(self):
        return Selector(self)

    def __apply__(self, event: DomainEvent):
        self.__stamp__(event)
        self.__route__(event)

        self.__changes__.append(event)

    def __stamp__(self, event: DomainEvent):
        event.__dict__.update({
            '__stream_id__': f'{self.__id__.id}:{self.__class__.__name__}',
            '__number__': self.__version__ + 1,
            '__timestamp__': time()
        })

    def __route__(self, event: DomainEvent):
        if event not in self.__seen__:
            self.__version__ = event.__number__
            self.__seen__.append(event)

            self.mutate(event)

    def mutate(self, event: DomainEvent):
        pass # pragma: no cover


class Selector:

    def __init__(self, aggregate: AggregateRoot):
        self.aggregate = aggregate
    
    def get_trace(self, trace_id: str, include_event_type: type = None):
        events = tuple([
            e for e in self.aggregate.__seen__
            if e.__trace_id__ == trace_id
        ])

        if include_event_type:
            events = tuple([
                e for e in events
                if isinstance(e, include_event_type)
            ])

        return events

    def get_trace_if_not_compensated(self, trace_id: str, compensate_type: type, include_event_type: type = None):
        events = self.get_trace(trace_id, include_event_type=include_event_type)
        
        compensated = any(isinstance(e, compensate_type) for e in events)

        if not compensated:
            return events
        else:
            return []
        

class mutator:

    def __init__(self, func):
        update_wrapper(self, func)

        self.func = func

        self.mutators = {}

    def __get__(self, obj, objtype):
        return partial(self.__call__, obj)

    def __call__(self, aggregate, event: DomainEvent):
        if event.__class__ not in self.mutators:
            return

        mutator = self.mutators[event.__class__]
        mutator(aggregate, event)

    def event(self, event_type: type):
        def inner_function(func):
            if event_type in self.mutators:
                raise DefinitionError(f'{event_type.__name__} mutator already defined near to {self.func.__qualname__}')

            self.mutators[event_type] = func
            return func
        return inner_function
    