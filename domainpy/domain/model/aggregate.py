
from datetime import datetime


class AggregateRoot:
    
    def __init__(self):
        self.id = None
        
        self.__version__ = 0
        self.__changes__ = []
    
    def __apply__(self, event):
        self.__stamp__(event)
        self.__route__(event)
        
        self.__changes__.append(event)
    
    def __stamp__(self, event):
        event.__dict__.update({
            '__aggregate_id__': self.id.id,
            '__number__': self.__version__,
            '__version__': 1,
            '__timestamp__': str(datetime.now())
        })
        
    def __route__(self, event):
        self.mutate(event)
        
        self.__version__ = self.__version__ + 1
    
    def mutate(self, event):
        pass
    
