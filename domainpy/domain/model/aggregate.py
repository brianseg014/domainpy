
from datetime import datetime

from domainpy.domain.model.value_object import Identity
from domainpy.domain.model.event import DomainEvent


class AggregateRoot:
    
    def __init__(self, id: Identity):
        if not isinstance(id, Identity):
            raise TypeError('id should be type of Identity')
        
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
            '__timestamp__': str(datetime.now())
        })
        
    def __route__(self, event: DomainEvent):
        if event not in self.__seen__:
            self.__version__ = event.__number__
            self.__seen__.append(event)

            self.mutate(event)
    
    def mutate(self, event: DomainEvent):
        pass
