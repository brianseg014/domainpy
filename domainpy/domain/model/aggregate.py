
from datetime import datetime

from domainpy.domain.model.value_object import Identity


class AggregateRoot:
    
    def __init__(self, id: Identity):
        if not isinstance(id, Identity):
            raise TypeError('id should be type of Identity')
        
        self.__id__ = id
        
        self.__version__ = 0
        self.__changes__ = []
    
    def __apply__(self, event):
        self.__stamp__(event)
        self.__route__(event)
        
        self.__changes__.append(event)
    
    def __stamp__(self, event):
        event.__dict__.update({
            '__aggregate_id__': self.__id__.id,
            '__number__': self.__version__,
            '__version__': 1,
            '__timestamp__': str(datetime.now())
        })
        
    def __route__(self, event):
        self.mutate(event)
        
        self.__version__ = self.__version__ + 1
    
    def mutate(self, event):
        pass
    
