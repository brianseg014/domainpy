
import time

from domainpy.domain.model.value_object import Identity
from domainpy.domain.model.event import DomainEvent
from domainpy.utils.traceable import Traceable


class AggregateRoot(Traceable):
    
    def __init__(self, id: Identity):
        if not isinstance(id, Identity):
            raise TypeError(f'id should be type of Identity, found {id.__class__.__name__}')
        
        self.__id__ = id
        
        self.__version__ = 0
        self.__changes__ = [] # New events
        self.__seen__ = [] # Idempotent
    
    def __apply__(self, event: DomainEvent):
        self.__stamp__(event)
        self.__route__(event)
        
        self.__changes__.append(event)
    
    def __stamp__(self, event: DomainEvent):
        event.__dict__.update({
            '__aggregate_id__': f'{self.__id__.id}:{self.__class__.__name__}',
            '__number__': self.__version__ + 1,
            '__version__': 1,
            '__timestamp__': time.time()
        })
        
    def __route__(self, event: DomainEvent):
        if event not in self.__seen__:
            self.__version__ = event.__number__
            self.__seen__.append(event)

            self.mutate(event)

    def __get_by_trace_id__(self, trace_id: str):
        return tuple([
            e for e in self.__seen__
            if e.__trace_id__ == trace_id
        ])

    def __get_for_compensation__(self, trace_id, event_type: type, compensate_type: type = None):
        events = self.__get_by_trace_id__(trace_id)
        filtered_events = tuple([
            e for e in events if isinstance(e, event_type)
        ])

        for e in events:
            print([e, e.__trace_id__])

        if compensate_type is None:
            return filtered_events
        else:
            return tuple([
                e0 for e0 in events
                if not any(
                    True for e1 in events 
                    if isinstance(e1, compensate_type)
                    and e1.__trace_id__ == e0.__trace_id__
                )
            ])
    
    def mutate(self, event: DomainEvent):
        pass
